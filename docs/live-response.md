# EVOLVE WITH ME: live-response backend (experimental)

The performance is built in Logic Live Loops: prepared beats and synths,
live Godin audio through Focusrite, layered vocals, and a MIDI controller.
SUZY//AI should respond to a phrase while that performance continues.

This service implements **the backend half** of that interaction. It accepts bounded
PCM chunks, responds in a background thread, and exposes audition/accept/discard
commands. The native Mac companion supplies dry capture, controller input, playback
and experimental MIDI-clock scheduling; see `mac-companion.md`. The Python service
itself does not capture or play sound. There is no AU or Live Loops cell insertion,
and hardware rehearsal remains required.

## Start

No new Python dependencies or models are required. From the checkout:

```bash
python3 -m suzy_ai.music.server --port 7333
```

For model-assisted decisions, start the **existing** SUZY//AI runtime separately
on 7332, using already installed model weights. The bridge defaults to
`http://127.0.0.1:7332/v1`; override with `--core-url` for another loopback port.
It calls `/v1/chat` with personal memory disabled, empty chat history, at most 1024 output tokens,
an eight-second client deadline, and a 16 KiB response limit. The existing core
retains its single inference slot and local protections. A busy/offline/invalid
model request fails explicitly; it is never silently relabelled deterministic.
A client deadline does **not** guarantee the backend stopped generating. Do not
retry repeatedly; a still-running core request will return busy to new requests.
The existing Mac launcher uses a 120-second backend timeout.

## Controller/capture protocol

All URLs below are on `http://127.0.0.1:7333`. Health/status report `protocol_version: 2`;
the current companion refuses an old bridge instead of sending incompatible config. Host/origin protections are inherited
from the existing core. No permissive CORS or external bind is added. Local native
clients may call the API; hosted browser pages may not. This trusts local processes
on the machine, like the existing core; it is not an authentication boundary
against another local process.

| Method / path | Body | Result |
| --- | --- | --- |
| GET `/health` | — | Process health; not model readiness |
| POST `/v1/live/capture` | JSON config below | 201, unique capture ID |
| POST `/v1/live/ID/chunks/SEQUENCE` | Raw PCM16LE, `application/octet-stream` | 200, next sequence |
| POST `/v1/live/ID/finish` | `{}` | 202, background processing |
| GET `/v1/live` | — | State, worker busy flag and response metadata |
| POST `/v1/live/ID/audition` | `{}` | Ready → auditioning |
| POST `/v1/live/ID/stop-audition` | `{}` | Auditioning → ready |
| POST `/v1/live/ID/accept` | `{}` | Ready/auditioning → accepted |
| GET `/v1/live/ID/audio.wav` | — | WAV only in auditioning/accepted state |
| POST `/v1/live/ID/discard` | `{}` | Drop audio; invalidate late results |

JSON actions require `application/json` and a Content-Length. Example arm body:

```json
{
  "sample_rate": 48000,
  "channels": 1,
  "bpm": 120,
  "mode": "evolve",
  "provider": "deterministic",
  "instruction": "Keep the opening recognizable; leave gaps for my voice."
}
```

Modes: `mirror`, `augment`, `evolve`. Providers: `deterministic` (default) or
`model`. Artist instruction is passed to the model provider only; deterministic
mode does not interpret it. BPM is supplied by the host, not inferred.

Capture is 44.1/48 kHz, mono/stereo, interleaved signed 16-bit little-endian PCM.
Each chunk is at most 65,536 bytes and contains whole frames. Sequence starts at
zero: duplicated/out-of-order chunks return 409 without being appended. The ID
protects against old controller commands affecting a new capture. The limit is
eight seconds (1.536 MB at 48 kHz stereo), with a 0.25-second minimum. Exceeding
the limit is rejected without truncation; the adapter must finish or discard.
The adapter must convert float audio to PCM16 off the real-time thread.

Only one capture/candidate exists. Arm is refused while capturing, processing,
ready or auditioning. Accept/discard/failed permits a new capture once the worker
has exited; copy accepted audio into the host first. Arming replaces the old
candidate. Discard clears visible audio immediately but does not forcibly kill
inference. Until the worker exits, new captures are refused. No work queues grow.

Audition/accept are **protocol states**, not playback instructions fulfilled by
this service. The host owns monitoring, launch timing, note/audio stop and transport.
`finish` replies without waiting for rendering/inference. Poll status at a modest
rate (e.g. 5 Hz); do not poll or perform HTTP on an audio callback.

## What produces the sound

The source is the musician's actual captured waveform. Analysis currently derives
level envelopes, host-tempo slice boundaries, energy-rise onsets and uncertain
monophonic pitch hints. It does not detect key, chords or lyrics.
There are at most 16 slices; long/fast phrases use coarser slices to retain that cap.
The final slice may be shorter. When a shorter source slice occupies a longer
output slot, its remaining space is silent; longer slices are cropped to the slot.
There is no time-stretching.

- Deterministic MIRROR retains slice order with short fades and reduced gain.
- Deterministic AUGMENT mixes dry audio with a quiet one-beat-delayed response.
  It is a texture, not inferred harmony; delayed material beyond the phrase ends
  is omitted.
- Deterministic EVOLVE rotates slice order; it is reproducible, not AI.
- Model mode proposes each source slice index, gain and reversal independently.
  It can repeat/reorder source material. Strict validation runs before rendering.
  No generated code, commands, paths or filter expressions are executed.

Model choices are neural text inference over measured features. Rendering remains
deterministic sample processing; this is **not neural audio generation** and the
model has not directly listened to the waveform. Provenance identifies the provider,
model (only when used), exact plan, source hash, measured features and elapsed time.

Output preserves sample rate, channels and duration, adds short edge fades and
caps sample magnitude at -3 dBFS. That ceiling is not a true-peak guarantee or a
mix limiter. Listening evaluation is still required. Nothing is auto-played.

## Failure and resource boundaries

Audio and results remain in bounded process memory, never in the private memory
DB, public repo or a temporary audio file. No automatic teaching, recording history
or publication occurs. Discard releases the visible candidate; an active worker
may retain its bounded source until completion. Process exit loses all candidates.

This Python buffer uses locks, allocations and copying. It is **not real-time safe**.
The native host must copy input into a preallocated bounded native buffer, then
send from a non-real-time worker. Do not call Python, HTTP, or inference from an
AU render block. A future adapter must drop/cancel a capture rather than block
when its producer queue fills.

The bridge does not open audio devices or control Logic transport, so stopping it
cannot directly remove Logic's audio graph. CPU/memory contention remains possible:
no guarantee against machine-wide overload is made. On an 8 GB M2, test with the
model stopped first; try concurrent inference only with a modest Logic session.
Keep accepted audio in Logic and rehearse with both AI services stopped.

## Validation and Mac companion

```bash
bash scripts/test.sh
```

Tests use generated musical tones and a fake local model/core, not model weights,
private recordings or audio hardware. They exercise PCM capture, HTTP lifecycle,
sequence/size limits, output duration, provider labels, model plan rejection,
late-result discard and client deadlines, plus the existing core suite.

The [Mac companion](mac-companion.md) provides dry system-input capture,
controller actions and response audition/loop playback alongside Logic. First validate
ordinary Godin/voice audio; 13-pin synth hardware is not required. A thin AU capture
component must compile and pass host testing in Xcode/Logic on the Mac. Choose and
verify the response playback/routing method before claiming automatic Live Loops
integration. Playback quantization belongs to the host's tempo/transport clock.

Mac acceptance gate: looping Logic backing continues while capturing, processing,
auditioning and deliberately stopping the bridge. Suzy can bring in a useful
response without Finder/Terminal interaction. Measure actual latency and listen
for clicks/dropouts. This gate has **not** been run in Linux.

### Musical context extension

Capture accepts optional `section` (64 characters), `key` (24), and `instruction` (500).
Status includes `performance_context`, limited to four accepted-decision summaries in
RAM. `POST /v1/live/context/reset {}` clears it without touching personal memory.
`audition` and `accept` are idempotent for their respective current states, allowing
clients to retry after a lost acknowledgment. Accept never duplicates a history entry.
The manifest includes bounded onset and monophonic pitch hints, supplied key/section,
and the context used for that proposal. These are deterministic analysis, not neural
waveform generation. The Mac companion now offers experimental clock scheduling;
see `docs/mac-companion.md` for fixed-tempo limits and required hardware QA.
