# Live Scarlett → SUZY//AI → MacBook audio probe (experimental)

**Goal:** test phrase-based live interaction while Logic keeps playing, without
exporting or importing WAV files, building Swift, or opening a new model.

**Status:** code + synthetic tests only. **NOT yet verified** on Suzy's Focusrite,
VE-22, Logic setup or 8 GB Mac. This is *not* continuous audio-to-audio neural
generation and is not ready for stage performance.

This standalone Python prototype opens one 48 kHz, stereo full-duplex PortAudio
stream, **waits for you to press Return and counts down three seconds**, captures
an eight-beat phrase in bounded memory, asks the existing
SUZY//AI session for a response, and plays the response once at reduced gain.
Each cycle automatically captures → waits for a proposed response → auditions it.
Logic's audio and transport remain independent.

## Before starting

1. Keep **Logic's normal audio output** selected. Input may be the Scarlett
   while output is the MacBook speakers or external headphones. The live probe
   can now select different input/output devices explicitly. At the first test,
   use low speaker/headphone volume and avoid acoustic or electrical feedback:
   speakers near a live microphone can cause a feedback loop.
2. The **mic → VE-22 → Focusrite** is the audio input. The **Keystation USB MIDI**
   goes to Logic, **not** this probe. The probe does not currently listen to
   Logic's MIDI instruments, internal buses, or the VE-22's MIDI.
3. In Terminal, from the updated repository:

   ~~~bash
   cd ~/Projects/suzy-ai
   .venv-mac/bin/python -m pip install -e '.[live]'
   .venv-mac/bin/python -m suzy_ai.music.live_probe --list-devices
   ~~~

   Optional dependency is only the small `sounddevice` Python/PortAudio binding;
   it does not need NumPy when using RawStream. Nothing touches Swift/Xcode.
   If the correct interface isn't the macOS default, select the device index
   shown in the list using `--device N` (it must support 2 inputs + 2 outputs).

## Pick your headphones or speakers before recording

The live prototype supports **separate Scarlett microphone input and listening
output**. If Logic is playing through your headphones but SUZY//AI seems to
come through speakers, don't guess which Core Audio device is active.

Use the **interactive output selector**:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device 0 --choose-output \
  --bpm 120 --beats 8 --cycles 1 \
  --mode mirror --provider deterministic --gain 0.3
~~~

The program lists available output devices (for example, **2 = External
Headphones**, **4 = MacBook Pro Speakers** on the original Mac setup). Enter a
number. It plays a quiet test tone on that device, then asks if you heard it
through the headphones or speakers you actually intend to use. Answer
**y** to confirm; **n** returns to the device list. Enter **q** to exit
without capturing anything.

Only after confirming the listening destination will it open the live
microphone stream and offer the normal **press Return → 3, 2, 1 → record**
workflow. Logic's selected audio output is not changed.

You can also continue using `--input-device 0 --output-device 2` (headphones)
or `--input-device 0 --output-device 4` (MacBook speakers) without the menu.
Device numbers may change after reconnecting devices. A successful tone on
one device doesn't guarantee the split-device duplex stream will audibly use
the same output, so verify with a real phrase afterward.

## Mono mic in both headphones (centered monitoring)

A Scarlett Solo microphone connected to **input channel 1** is a **mono
source**; the second interface input can legitimately be silent. Earlier
versions preserved that left-only channel and played silence to the right
ear. This is not a headphone defect or a model-inference problem.

The new `--output-mix` setting works on the *AI response* after processing,
**outside** the live audio callback:

- `--output-mix auto` (default): if a response is present in only one
  channel, duplicate that channel into **both L and R** at the same amplitude.
  Preserve independent L/R when both channels contain signal.
- `--output-mix mono-center`: explicitly use the louder channel in **both
  headphones**. Useful for one mic in either Scarlett socket.
- `--output-mix stereo`: never fold the channels; keep original independent
  stereo (including a silent side if your input was mono).

This produces **dual-mono in a stereo headphone stream**, not fake stereo
width or two different takes. Future stereo vocal FX from the VE-22 can
remain stereo, and we can add creative panning/width separately.

Example with confirmed external headphones (device 2 on the first Mac test):

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device 0 --output-device 2 \
  --output-mix mono-center \
  --bpm 120 --beats 8 --cycles 1 --countdown 3 \
  --mode mirror --provider deterministic --gain 0.3
~~~

The Terminal prints `Output mix: centered mono ... into L+R` and
equal left/right output peaks. Listen to verify both headphone sides.
Keep listening volume low. When using the interactive `--choose-output`
option, the same `--output-mix` setting applies after you confirm the tone.

## Debug audio output before recording

The first hardware runs confirmed a nonzero Scarlett channel 1 input and
successful response processing, but **no audible output**. GitHub/terminal
success messages are not proof of audibility.

First verify the selected playback device without singing or opening the
microphone:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe --test-output --output-device 2
~~~

This plays a **quiet, faded 440-Hz tone on both stereo channels** to
`External Headphones` (device 2 on the original device list). Lower the
listening volume first. If the tone is inaudible, try
`--test-output --output-device 4` for MacBook Pro Speakers. The preferred
output is whichever one you really listen to in Logic, which may differ
from the Mac's internal speaker device. No input is captured in this test.

When a tone is audible, run the full experiment using the **same** output
index, beginning with `--gain 0.3` and a low physical volume. Look at the
new `Output levels` line (peak and RMS after DSP/gain), the physical
output device name, the playback frame counts, and stream-warning count.
A driver callback writing all frames still doesn't prove the signal was
audible in the room.

We do not log microphone waveforms or upload audio to GitHub. Share the
Terminal text only.

## First hardware run: isolate routing from model quality

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device 0 --output-device 2 \
  --output-mix auto --bpm 120 --beats 8 --cycles 1 --mode mirror --provider deterministic --gain 0.3
~~~

- Device **0** is Scarlett Solo USB input. Device **2** was External
  Headphones (the Mac's default output) and device **4** was MacBook Pro Speakers
  on Suzy's Oct 21 list. The test tone identifies which is audible. Pass
  that device as `--output-device`. Device indices can
  change between sessions, so check `--list-devices` again if needed.
- Change **120** to your Logic BPM.
- **No recording in Logic is necessary.** Keep Logic playing normally. The
  probe listens directly to the Scarlett microphone input. Press **Return in
  Terminal** when ready, watch the **3, 2, 1 countdown**, then sing **after**
  `RECORDING NOW`. At 120 BPM, eight beats provide a four-second window.
  Nothing is captured until the countdown ends; no WAV files are saved.
- After capture the probe prints input peak and RMS for Scarlett channels 1 and 2.
  If both are near zero, check the VE-22 audio output, Scarlett input gain,
  channel and Terminal microphone permission. It also warns about clipping.
- If you want two tries, change `--cycles 1` to `--cycles 2`: the second cycle
  waits for your next Return. `--countdown 0` disables the countdown.
  Playback is automatic after processing.
- This is **not** quantized to Logic's bar/beat boundaries. The first capture
  starts with a stream callback, not a MIDI clock.
- `--cycles 0` keeps offering new capture cycles (each requires Return)
  until Ctrl-C. **Ctrl-C** closes this probe's stream and stops its audio; Logic
  is not intentionally stopped.
- Set `--gain 0.1` if needed for safer playback. Default is 0.3;
  gain above 0.5 is intentionally rejected.
- On macOS, grant microphone access to your Terminal application if requested.

If you hear an effect, it is *deterministic* audio processing, not a model.
That validates input capture, buffer handoff and audio output before we add Qwen.

## Experimental vocal duet: use your *actual humming*, not a synth

The Frère Jacques rehearsal confirmed real Qwen note decisions and a
four-repeat layer, but the synthesizer produced only four fixed-gesture
tones rather than a copy of the singer's sound. A text-only Qwen3 1.7B
model **cannot imitate a raw vocal waveform or invent a new sung phrase**.

Try the new optional **sampled-vocal layer** instead:

~~~bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.live_probe --test-model \
  --provider model --ai-reply vocal
~~~

This calls real local Qwen with a synthetic phrase, no microphone or
speakers. It validates that Qwen chooses exactly one real-voice gesture:
`vocal-canon` (a one-beat delayed copy of the singer), `vocal-echo`
(two-beat delayed copy), `vocal-stutter` (short hummed fragments) or
`vocal-reverse` (each beat backwards). The audio engine uses **the
recorded vocal samples themselves**, with short fades and fixed limits.
The resulting response has an independent voice layer over a quieter
copy of the original phrase and repeats for the requested number of
cycles. It is sampled-audio editing, **not neural voice cloning**.

Once that smoke test passes, sing a Frère Jacques phrase through the
Focusrite, with your headphones kept at low volume and Logic monitoring
your new singing:

~~~bash
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device "Scarlett Solo USB" --choose-output \
  --output-mix mono-center --bpm 120 --beats 8 \
  --mode evolve --provider model --ai-reply vocal \
  --layer-repeats 4 --cycles 1 --gain 0.3
~~~

Look for `QWEN VOCAL ANSWER: vocal-...` and the repeated 4-second
response. It should sound like **your actual humming arranged in a
second part**, not only four synthesized notes. The chosen texture
might still be quite simple; the model chooses the edit, and DSP
makes the audio.

**Crucial limits:** the Python probe *does not continue recording*
while its candidate repeats, so your new singing is heard via Logic
but is not fed back into Qwen until you start another cycle. It has
no separate persistent accepted layer, real-time pitch-preserving
voice transformation, new lyric generation, MIDI clock sync or
neural audio generation. Treat it as a prototype only. The repo's
native [Mac looper](local-looper.md) has real repeat, overdub and
layer acceptance, but needs suitable same-device I/O and hardware
rehearsal before performance. Do not confuse this Python texture
with continuous AI listening.

## NEW: Hear Qwen add *new notes* to your voice (experimental)

The successful source-loop test showed `AI-directed source beat order:
[1, 2, 3, 4, 5, 6, 7, 0]` and four repeats. The model chose a
one-beat rotation of your recording; there were **no new notes**.

The new opt-in `--ai-reply notes` mode asks Qwen to choose one compact
**call-and-response interval gesture** (`answer-fifth`, `answer-third`,
`answer-below` or `answer-octave`). The Python DSP detects a *rough,
monophonic* sung pitch, creates sparse, quiet new synthesizer notes around
that pitch and mixes them with your recorded phrase. The model selects
the gesture; it **does not hear raw audio or synthesize waveform samples**.

First validate the model on a generated tone, without your mic or speakers:

~~~bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --test-model --ai-reply notes --provider model
~~~

Pass criteria: `MODEL SMOKE PASS`, plus a `Qwen note choice:` and
nonempty `synthesized MIDI notes=` list. The model and audio engine must
pass the new note-specific contract, not just the original beat reorder.

Then try a clean, **sustained, single-note** opening phrase with the
existing Scarlett + VE-22 mic, Logic live monitoring and quiet headphones:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device "Scarlett Solo USB" --choose-output \
  --output-mix mono-center --bpm 120 --beats 8 \
  --mode evolve --provider model --ai-reply notes \
  --layer-repeats 4 --cycles 1 --gain 0.3
~~~

Select the headphones, confirm the test tone, press Return, sing for
four seconds, and continue singing over the repeating **original plus
new-note response**. The log says `QWEN ANSWER: answer-...`,
lists the resulting MIDI note numbers and confirms the new note audio
is mixed. The notes should be different from a plain replay.

If `NO NOTE ANSWER` appears, the input didn't give reliable
single-note pitch estimates; **no note is guessed or injected**. Try
one held vowel away from Logic playback (headphones prevent bleed),
moderate Scarlett input gain, and avoid strong vocal effects during
capture. If Qwen doesn't return an allowed gesture, the operation
fails explicitly rather than secretly playing a canned melody.

The pitch detector is heuristic and can mishear vibrato, harmonies,
chords, strong VE-22 processing and noisy takes. The synth is a
simple low-level two-harmonic sound with short fades and a -6 dBFS
mix ceiling, generated *outside the audio callback*. Its notes are
placed on alternate supplied beat slots, but the resulting audio
is **not synchronized** to Logic's transport. Don't turn up
headphone volume to overcome quiet responses without checking peaks.

**Not continuous real-time interaction:** one four-second capture leads
to one model decision and a finite repeated layer. The model **cannot
hear your continuing vocals while that layer plays**, and it does not
replace an established loop on the fly. Continuous listening and
boundary-quantized layer exchange need a separate performance-safe
audio/MIDI integration. This is a rehearsal-only experiment.

## Hear a response play *over* your continued performance

The earlier tests only played one response once, after your captured phrase.
That is not accompaniment. The new optional `--layer-repeats` setting can
repeat the finished response up to eight times **while you continue singing or
playing the Logic session**. Logic must already be monitoring your live voice;
the Python probe does not route or mix your dry microphone signal.

**First prove the layering with deterministic processing**, keeping headphones
at a low level:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device "Scarlett Solo USB" --choose-output \
  --output-mix mono-center --bpm 120 --beats 8 \
  --mode evolve --provider deterministic \
  --layer-repeats 4 --cycles 1 --gain 0.3
~~~

Select the headphones you can hear, confirm the tone, press Return for the
countdown and sing an initial four-second phrase. Then **keep singing over
the response as it repeats four times** (16 seconds at 120 BPM), or press
Ctrl+C to stop the probe. No new input is captured during those repeats.
This verifies the audio layer and that Logic continues running. These
deterministic EVOLVE edits are a source-slice rotation, **not AI**.

**Then try model-guided variation** with the existing local Qwen core running
on port 7332:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device "Scarlett Solo USB" --choose-output \
  --output-mix mono-center --bpm 120 --beats 8 \
  --mode evolve --provider model --layer-repeats 4 \
  --cycles 1 --gain 0.3 \
  --instruction "Make a sparse, rhythmic four-beat variation with gaps for my singing."
~~~

The console must say `provider=model` with a real model name for this test
to demonstrate model use. Qwen receives audio **features** and chooses
bounded source-slice reorder/reverse/gain operations. It does not hear the
raw waveform or synthesize an independent harmony. The new loop plays
those transformed source slices, not new notes.

**Limitations:** The response begins after the 4s capture and model/render
delay, without Logic bar/clock synchronization; it may start off-beat.
The repeat can drift relative to Logic, especially when the speaker and
Scarlett run on independent hardware clocks. The waveform has short source
slice fades but it does not promise seamless boundary transitions. The
probe cannot capture another phrase while the response loops, cannot add
multiple AI layers or send MIDI notes into Logic, and has no footswitch.
This is a rehearsal-only first layer test, **not** a validated stage setup.

## Compact Qwen music choices

The first real `--test-model` failed in **plan validation**: Qwen supplied
an arrangement whose slice list was not as long as the eight beat-slices in
the input. Previous prompts incorrectly demonstrated one slice in JSON
while asking for eight, which made the model's bookkeeping needlessly hard.

Now Qwen only needs to pick **one rhythmic pattern**, as a single tiny JSON
object, e.g. `{"pattern":"stutter"}`. Its accepted choices are `rotate`,
`stutter`, `reverse` and `mirror`. The local engine converts that explicit
model choice into all eight beat-slice instructions and validates every one
before rendering. It **never pads an invalid legacy array**, invents a model
choice after a failed response, or silently replaces Qwen with deterministic
mode. Unrecognized model output still fails safely.

Only a compact, measured musical sketch (beat energy and onset count plus
the performer's instruction) is supplied to Qwen, without the audio
waveform, lyrics or personal memory. This makes the prompt smaller for
the 8 GB Mac's local model. After a successful live model run, the probe
prints the actual source beat order that was rendered. These are edited
source slices, **not neural synthesis or newly composed harmony**.

With your existing local service already running:

~~~bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.live_probe --test-model
~~~

If `MODEL SMOKE PASS` prints, try the existing live `--provider model
--layer-repeats 4` command. If not, paste the *new specific diagnostic*
rather than repeating microphone captures.

## Diagnose a model error *without singing again*

The local Core API may reply to a quick chat request successfully, yet a
musical arrangement can still fail if Qwen exceeds the eight-second planning
deadline, returns non-JSON output, or proposes an invalid slice plan. Audio
routing and microphone levels can be fine while model planning fails.

With the **existing** local SUZY//AI core on `127.0.0.1:7332` and
`llama-server` on `127.0.0.1:8082`, run:

~~~bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.live_probe --test-model
~~~

This uses a **synthetic four-second test tone**, the same eight beat-slices
as a vocal capture. It does **not open the microphone, make sound or export
audio**, and still requires the local Qwen service. It submits musical
features with personal memory disabled, validates the returned plan and
prints a clear success or a safe failure category.

Example failures, not necessarily what happened on Suzy's Mac:

- `response failed during model planning: local model request timed out
  (8-second deadline)`: inference didn't finish quickly enough.
- `response failed during model planning: model replied with non-JSON
  arrangement`: model responded, but not in the required JSON format.
- `response failed during plan validation: plan must preserve the number
  of source slices`: model-generated JSON parsed but violates the strict
  arrangement contract.
- `local core busy (HTTP 429)`: don't send another request while the
  existing one is still occupying the core's single inference slot.

All model-debug output is restricted to fixed failure categories. No raw
model text, private prompts, mic recordings or tokens are printed. The
existing live-probe exception message also no longer incorrectly blames
Core Audio on a model-planning failure.

Only return to `--provider model --layer-repeats 4` **after the synthetic
test passes**. Do not restart an already-working local SUZY//AI service
just because a musical arrangement fails.

## Then test real Qwen model *decisions*

In one Terminal (existing model setup; no additional download):

~~~bash
cd ~/Projects/suzy-ai
bash scripts/start-mac.sh --api-port 7332 --model-port 8082 --no-chat
~~~

Leave it running. In a second Terminal:

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device 0 --output-device 2 \
  --bpm 120 --beats 8 --cycles 1 --mode evolve --provider model --gain 0.3
~~~

The model receives measured features, not raw audio, and chooses slice order,
gain and reversal. WAV rendering remains deterministic. A failed or timed-out
model response is **an error**, never silently replaced with fake AI.
Personal memory is disabled for model decisions.

## QA observations to report

| Case | Record |
| --- | --- |
| Input | Which Scarlett channel shows a level? Is the mic clearly audible? |
| Output | Which device plays the test tone? Are equal L/R peaks printed after mono-centering, and do both ears hear the response? |
| Round trip | Time printed between capture end and response ready |
| Timing | Does the response align *musically*, despite no Logic clock sync? Does the 4x repeat play while you keep singing through Logic? |
| Stability | Any device warning callbacks, missing playback frames, clicks or Logic glitches? |
| AI provenance | Does the log explicitly say `provider=model` for model runs? |
| Stop safety | Does Ctrl-C silence this probe without stopping Logic? |

Do not assume a silent or apparently successful run passed. Capture the
terminal's device list, error, response time and subjective observations.

## Known implementation limits

- A Python callback copies audio buffers and uses the GIL. Although no inference,
  networking or disk writes occur in that callback, **this is not guaranteed
  real-time safe**. Don't use this prototype onstage.
- One stereo input buffer (the Scarlett may have mic on only one channel), one response at a time, no dry pass-through, no private
  audition/cue bus, no MIDI control, no overdub or time-stretch.
- This is a **phrase capture → model decision → one-shot response** pipeline,
  not continuous neural audio generation. Inference happens after the capture
  closes, so response time can be seconds.
- No Logic clock sync or sample-accurate alignment. `--bpm` sets phrase
  duration and analysis slices, **not** playback transport alignment.
- Input and output must both support stereo 48 kHz. **Two different physical
  devices may have independent hardware clocks**: PortAudio/Core Audio may
  refuse this duplex combination, or drift may degrade longer runs. An
  Aggregate Device or independent streams with resampling may eventually be
  needed. A stream-opening error is a hardware QA finding, not a pass.
- CPU/memory contention from Qwen could still make Logic glitch on an 8 GB Mac.
- The current response processor can reorder/reverse/attenuate *source slices*;
  it does not synthesize new melodies or harmonies.
- Nothing is exported or saved; unsaved audio is lost at exit.
- No audio is sent to public GitHub. No source or response WAV is committed.

## Developer checks (without audio hardware)

~~~bash
python3 -m unittest tests.test_live_probe -v
bash scripts/test.sh
~~~

Next after hardware QA: calibrated routing, a dedicated Stop control, MIDI
controller mapping, Logic synchronization/IAC, and better response synthesis.
The existing native companion is a separate implementation; it still has to
pass on-device timing tests and does not become validated by this probe.
