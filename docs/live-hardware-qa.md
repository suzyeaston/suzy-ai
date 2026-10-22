# Live Focusrite → SUZY//AI → Focusrite probe (experimental)

**Goal:** test phrase-based live interaction while Logic keeps playing, without
exporting or importing WAV files, building Swift, or opening a new model.

**Status:** code + synthetic tests only. **NOT yet verified** on Suzy's Focusrite,
VE-22, Logic setup or 8 GB Mac. This is *not* continuous audio-to-audio neural
generation and is not ready for stage performance.

This standalone Python prototype opens one 48 kHz, stereo full-duplex PortAudio
stream, captures a BPM-length phrase in bounded memory, asks the existing
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

   Optional dependency is only the small \`sounddevice\` Python/PortAudio binding;
   it does not need NumPy when using RawStream. Nothing touches Swift/Xcode.
   If the correct interface isn't the macOS default, select the device index
   shown in the list using \`--device N\` (it must support 2 inputs + 2 outputs).

## First hardware run: isolate routing from model quality

~~~bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m suzy_ai.music.live_probe \
  --input-device 0 --output-device 4 \
  --bpm 120 --beats 4 --cycles 2 --mode mirror --provider deterministic
~~~

- Device **0** is Scarlett Solo USB (2 inputs, 2 outputs) on Suzy's Oct 21
  list. Device **4** is MacBook Pro Speakers. To use the currently listed
  External Headphones instead, pass `--output-device 2`. Device indices can
  change between sessions, so check `--list-devices` again if needed.
- Change **120** to your Logic BPM.
- At 120 BPM, each capture lasts two seconds (four quarter-note beats).
- Begin singing as the terminal prints "recording now". The stream is open for
  the whole test; audio is captured and the response is played automatically.
- This is **not** quantized to Logic's bar/beat boundaries. The first capture
  starts with a stream callback, not a MIDI clock.
- Two cycles repeat the capture/AI/audition flow. \`--cycles 0\` keeps cycling
  until Ctrl-C. **Ctrl-C** closes this probe's stream and stops its audio; Logic
  is not intentionally stopped.
- Set \`--gain 0.1\` if needed for safer playback. Default is 0.3;
  gain above 0.5 is intentionally rejected.
- On macOS, grant microphone access to your Terminal application if requested.

If you hear an effect, it is *deterministic* audio processing, not a model.
That validates input capture, buffer handoff and audio output before we add Qwen.

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
  --input-device 0 --output-device 4 \
  --bpm 120 --beats 4 --cycles 2 --mode evolve --provider model
~~~

The model receives measured features, not raw audio, and chooses slice order,
gain and reversal. WAV rendering remains deterministic. A failed or timed-out
model response is **an error**, never silently replaced with fake AI.
Personal memory is disabled for model decisions.

## QA observations to report

| Case | Record |
| --- | --- |
| Input | Did it capture the VE-22 mic and correct Focusrite channels? |
| Output | Did the response play from wired headphones through Focusrite? |
| Round trip | Time printed between capture end and response ready |
| Timing | Does the response align *musically*, despite no Logic clock sync? |
| Stability | Any "Device warning callbacks", clicks, dropouts or Logic glitches? |
| AI provenance | Does the log explicitly say \`provider=model\` for model runs? |
| Stop safety | Does Ctrl-C silence this probe without stopping Logic? |

Do not assume a silent or apparently successful run passed. Capture the
terminal's device list, error, response time and subjective observations.

## Known implementation limits

- A Python callback copies audio buffers and uses the GIL. Although no inference,
  networking or disk writes occur in that callback, **this is not guaranteed
  real-time safe**. Don't use this prototype onstage.
- One stereo dry input, one response at a time, no dry pass-through, no private
  audition/cue bus, no MIDI control, no overdub or time-stretch.
- This is a **phrase capture → model decision → one-shot response** pipeline,
  not continuous neural audio generation. Inference happens after the capture
  closes, so response time can be seconds.
- No Logic clock sync or sample-accurate alignment. \`--bpm\` sets phrase
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
