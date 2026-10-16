# Local looper with optional background AI

Play the native looper with AI disconnected or disabled. Logic continues its prepared
Live Loops backing. Launch without Python or a model:

```bash
bash scripts/start-mac-companion.sh --looper-only
```

## Interface setup

Select the **same full-duplex stereo interface** (such as the Focusrite) for macOS
input and output. Use 44.1 or 48 kHz. The app uses channels 1/2 and requires Float32
virtual streams; unsupported devices fail visibly. Separate built-in mic/output,
Bluetooth and aggregate-device arrangements are outside this first implementation.
The app never changes the device's rate, buffer size or Logic's audio settings.

Monitor live guitar/vocals through the interface or Logic. The looper outputs the
recorded loop, not live input monitoring. Avoid sending its output back to its input.

## Playing

- **Record:** capture 0.25–8 seconds. Press again to finish in free mode; beat-length
  recording finishes automatically. The C audio callback starts repeating on the
  next frame after capture closes, even within the same audio block. No recording
  file is finalized and no new player is started between these stages.
- **Overdub:** arm one cycle at the next loop boundary. The existing mix keeps
  playing while input is written into a spare buffer at compensated loop positions.
  At cycle completion, pointers swap; the next frame uses the completed mix.
  Input/output timestamp separation is frozen for that take. The capture window
  includes the interface's input lead relative to output; play continuously across
  the boundary. This is not calibration for Logic plug-in or monitoring latency.
- **Undo:** restore the preceding mix at a loop boundary, or immediately while
  stopped. One undo is retained. Mute preserves phase.
- **Stop:** cancel unfinished recording/overdub and silence this app at the next
  audio callback; accepted local audio remains available. Play resumes with free
  timing. Clear removes the original and undo, and invalidates pending AI proposals.
- **Save original:** save the latest exported WAV. Export follows the audio commit
  asynchronously; wait for the snapshot-ready message before saving a recent take.
  Unsaved audio is lost on exit. Interface failure preserves only the last export.

This is one loop with overdubs, not independently editable tracks. Summing saturates
at +/-1; leave input headroom. No automatic seam crossfade is applied yet, so abrupt
phrase endpoints can still click even though playback has no file-start gap.

## Background AI

Enable AI, Connect, and choose deterministic DSP or local-model decisions. Committed
recordings, overdubs and undo produce immutable WAV snapshots. Audio playback never
waits for snapshot encoding, HTTP or inference. There is one export worker and one
bounded snapshot buffer; slower consumers do not accumulate audio jobs.

A changed source or new variation request cancels unaccepted proposals, **not the
accepted AI layer**. Turning background AI off stops new requests and invalidates
proposals while accepted music continues. Use **Remove AI layer** to stop it while
keeping the original. Stop All and explicit bridge reset also stop the AI layer;
clock safety handling can stop synchronized playback on transport/clock loss.

Add AI layer schedules the selected variation against the original's phase. It does
not overwrite the original or its undo. AI playback still uses the existing separate
AVAudioPlayer path: its replacement uses a UI timer and can overlap during UI stalls.
It is not yet part of the C render engine. Audition shares the audience output.

Only one proposal is active. An occupied backend can reject a new request visibly;
Request variation retries when it becomes available. Deterministic DSP is never
labelled as neural audio generation.

## Controller mapping

| Note (channel 16 by default) | Action |
| --- | --- |
| 36 | Record / finish original |
| 37 | Audition AI on shared output |
| 38 | Add AI layer |
| 39 | Stop all |
| 40 | Discard AI candidate |
| 41 | One-cycle overdub |
| 42 | Undo last overdub |
| 43 | Mute/unmute original |
| 44 | Clear original and invalidate proposals |
| 45 | Play stopped original |
| 46 | Remove accepted AI layer |

Escape is Stop All. Mouse controls and MIDI work without a bridge connection.

## Implementation and resource bounds

`NativeLoop/Loop.c` owns audio state on the CoreAudio IOProc thread. A bounded atomic
mailbox carries commands; Stop has a separate priority flag. No Swift, heap allocation,
file I/O, locks or networking runs inside the render callback. Only this app's IOProc
is started/stopped. Device rate, buffer-size, stream or alive changes cause a visible failure requiring Clear
and reconnect; the app does not reconfigure the device or stop Logic's IOProc.

Four preallocated stereo Float32 buffers (current, spare, undo, export) use about
12.3 MB at the eight-second/48 kHz maximum, plus small I/O scratch arrays. Snapshot
copying is limited to 4096 frames per callback. One control-thread copy and one
background WAV encoder add bounded temporary storage. Retained WAVs, AI players,
Python and model memory are additional; this is not a whole-app memory measurement.

The UI timer displays status, invalidates proposals and collects completed exports;
it does not close recordings, advance playback or commit local overdubs/undo.
Manual commands take effect on the next audio block. Experimental Logic/IAC scheduling
still has MIDI delivery jitter and no continuous drift correction. Hardware timestamp
compensation is implemented, but actual guitar/vocal alignment remains unmeasured.

## QA gate before performance use

Automated C tests exercise within-block first repeat, repeated playback, compensated
impulses, overdub/undo, cancellation, immutable snapshots, command limits and scheduled
boundaries with address/undefined-behavior sanitizers. Swift regression tests check
accepted-layer preservation. CI compilation is not a listening test.

1. At both 44.1/48 kHz, record clicks and real guitar/vocals; measure first-repeat
   continuity and overdub alignment against Logic. Try the intended buffer size.
2. With AI off, record, overdub twice, undo, mute, stop/resume and save. Stop midway
   through an overdub; confirm the original and previous undo survive.
3. Accept an AI layer, overdub the original, request another variation, disable AI,
   and clear the original. The accepted layer must continue until explicitly removed.
4. Stall/stop the bridge while playing. Local controls and accepted music must work.
5. Deny microphone access, disconnect the interface and change its rate. Confirm a
   visible error and that Logic's own processing has not been stopped by the app.
6. Run the full 15 minutes with Logic and, separately, with the local model enabled.
   Measure drift, peak CPU, memory pressure and clipping in the combined mix.

Keep this change in draft until Mac listening QA is complete. Use Logic's own looping
for the show if native timing is not musically acceptable.
