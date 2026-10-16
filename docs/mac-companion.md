# SUZY // LIVE — first Mac companion

This is an experimental native Mac app for the EVOLVE WITH ME performance. It
captures dry audio from the **macOS default input**, sends it to the live-response
backend, and plays the returned source-audio response through the **macOS default
output**. Logic continues to own its Live Loops, instruments and transport.

This is not an Audio Unit. It does not read Logic buses/effects or insert a Live
Loops cell. Free mode starts immediately; experimental Logic/IAC clock mode schedules
capture and response starts on a bar boundary. Read the timing limits and QA section below.

## Tomorrow's first launch

Requirements: macOS 13+, Xcode Command Line Tools (Swift 5.9+), Python 3.11+ and
this checkout. No new models, audio drivers, MIDI converters or Python audio
packages are installed by these scripts.

```bash
bash scripts/start-mac-companion.sh
```

The script builds an ad-hoc-signed app in `build/SuzyLive.app`, starts the bridge
on 7333 if none is running, and opens the app. Keep the terminal open. Quitting
the app stops only the bridge that this script started. An existing bridge is
reused only when its protocol version matches, and never killed. Quit an old bridge
from the previous version before starting this checkout. It does not start/download a model. For model mode use
the existing core on 7332 in another terminal. Start with deterministic mode.
`SUZY_PYTHON` can select a Python executable; otherwise `.venv-mac/bin/python` is
used if present, then `python3`.

To compile without launching or opening an audio device:

```bash
bash scripts/build-mac-companion.sh
cd apps/macos
swift test
```

If tools are missing, run `xcode-select --install` yourself. This script does not
install them. Local ad-hoc signing is for development; there is no notarized release.
A rebuild may require granting microphone permission again. Use System Settings →
Privacy & Security → Microphone if access is denied.

## Audio setup

1. In macOS System Settings → Sound, select Focusrite as input and output.
   Confirm the interface rate in Audio MIDI Setup; use 48 kHz for the initial test.
2. In Logic, independently select the Focusrite and play a simple backing loop.
3. Plug Godin's normal quarter-inch audio output and/or your microphone into the
   appropriate Focusrite input. No 13-pin MIDI connection is needed.
4. In the companion choose Channel 1, Channel 2, or stereo. It requests stereo
   48 kHz PCM recording from the default device, then extracts the selected input.
   Verify channel mapping on your exact interface; no input-device configuration
   is changed by this app. Built-in mic testing may duplicate/mix channels.
5. Use headphones. Monitor your live input through Logic **or** interface direct
   monitoring as appropriate; the companion does not monitor dry input. Its output
   is response audio only. Avoid double monitoring and acoustic recapture.

The first implementation uses AVAudioRecorder/AVAudioPlayer so Apple handles
capture and playback scheduling. No Python/HTTP operations run in a custom audio
render callback. Recorder capture goes to one private temporary WAV, is parsed and
uploaded automatically, then removed. No manual file export/import is required.
Ordinary stop/discard/quit removes the temporary directory; a forced termination
can leave it in the macOS temporary directory (`suzy-live-<UUID>`). The directory
has mode 0700. Responses stay in memory unless explicitly saved with Save WAV; unsaved responses are lost on exit.

## Performance controls

- **Capture** in free mode starts a 2, 4, 6 or 7.5 second recording. Press again to finish early.
  Backend minimum is 0.25 seconds. The 7.5 second option leaves headroom below
  the backend's eight-second limit for recording-buffer timing.
- **Audition** plays once on the shared output, after acknowledgment.
- **Bring in / loop** accepts and loops immediately in free mode (next bar in clock mode), replacing the previously
  accepted loop. It does not mute Logic or reset its playhead.
- Capture another phrase while an accepted loop keeps playing. There is one
  accepted loop and one candidate audition, not an unlimited layer stack.
- **Discard** clears the pending candidate but leaves the accepted loop playing.
- **STOP ALL / Escape** immediately stops all companion audio and capture before
  any network operation. Logic playback is untouched. Remote cleanup may finish
  later or fail; the local stop still works.
- **Reset bridge** is explicit recovery for an orphaned capture after a crash.
  It asks before discarding the bridge's current phrase. Use one companion client.

Keyboard shortcuts while the app is focused: C capture/finish, A audition, B bring
in, Escape stop. Letter shortcuts are disabled while text fields are focused. MIDI works without app focus.

## MIDI controller

Choose one CoreMIDI input source (default Off), then a channel (default **16**).
Only positive-velocity Note On messages trigger actions. Note numbers—not octave
labels—are authoritative:

| Note | Action |
| --- | --- |
| 36 | Capture / finish |
| 37 | Audition |
| 38 | Bring in / loop |
| 39 | Stop all companion audio |
| 40 | Discard candidate |

Set pads/buttons to these notes and the selected channel. The app does not send
MIDI or change the controller's assignments. Logic may also receive the same MIDI
messages; reserve this channel/range and prevent it from playing unintended Logic
notes or duplicate Live Loops commands. Hot-plugged controllers require Refresh
and selection. This first version uses CoreMIDI's MIDI 1 compatibility input API.

## What AI means here

The first PR's distinction remains: deterministic source-audio DSP versus a local
model choosing per-slice order, repetition, reversal and gain. It is not neural
waveform generation or melody/harmony understanding. The app displays the actual
provider and turnaround time; invalid/offline/busy model responses fail explicitly.

## QA checklist, in order

1. Build succeeds; launch app; grant microphone permission; Connect succeeds.
2. With Logic backing playing and the model stopped, capture each required input.
   Verify correct channel and audible, recognizable response. No input monitoring
   is added by the app.
3. Audition once; Bring in loops; capture a second phrase while that loop plays;
   discard it; confirm first loop remains. Accept a new one and verify replacement.
4. Press Stop while recording, uploading, waiting for a response and playing.
   Confirm local silence immediately and that late replies cannot start playback.
5. Stop the bridge during response playback; Stop must still silence the app.
   Restart bridge, Connect, and explicitly Reset if needed.
6. Choose controller, verify all five actions and note-off/velocity-zero behavior.
   Check Logic does not accidentally trigger instruments from reserved controls.
7. Only then test local model mode. Note turnaround, memory pressure and any
   glitches with the actual Logic project. Stop AI if it affects recording.
8. Save musical takes in Logic. This app is not a recorder/archive for the set.

Mac builds/tests can validate source and helper behavior, but interface access,
permissions, controller mapping, latency, sound quality and coexistence with Logic
still require Suzy's hardware QA. Passing Linux backend tests cannot establish those.

Apple API references:
- https://developer.apple.com/documentation/avfaudio/avaudiorecorder/record(forduration:)
- https://developer.apple.com/documentation/avfaudio/avaudioplayer/numberofloops
- https://developer.apple.com/documentation/coremidi/midiinputportcreatewithblock(_:_:_:_:)

## Performance reliability, clock and musical context

This update is experimental until tested with Suzy's actual Logic/Focusrite setup.

- A failed response preparation/start preserves the existing loop. Retrying Bring in
  is safe after a lost backend acknowledgment. For scheduled replacement, the old
  loop remains until the launch boundary; Stop cancels both pending and active audio.
- MIDI is decoded into a bounded 256-event inbox. Overflow explicitly stops companion
  audio and clears parser state instead of silently dropping a Stop or corrupting
  MIDI running status. The mouse Stop remains available if the controller disconnects.
- **Audition is not a private cue.** It uses the same default output as accepted audio.
  Acknowledgment is required before either the button or MIDI audition will sound.
  Use headphones for rehearsal. A private stage cue needs explicit separate output
  routing and hardware with suitable outputs; it is not implemented here.
- Save WAV saves a candidate (without sounding it), or the last accepted response when
  no candidate exists. Choose the destination in the native save dialog. No automatic
  private audio persistence or repo writes. Saved WAV files can be dragged into Logic
  for later arrangement; live use still requires no manual file round trip.

### Experimental Logic clock setup

1. In Audio MIDI Setup → MIDI Studio → IAC Driver, enable the driver and create a bus
   named `SUZY Clock`. This is virtual MIDI, with no new hardware needed.
2. In Logic → File → Project Settings → Synchronization → MIDI, choose that bus as a
   destination and enable Clock. Use **Song – SPP at Play Start and Stop/SPP/Continue
   at Cycle Jump** for the first test. Keep Logic the transmitting clock leader.
3. In the companion, Refresh MIDI, choose `SUZY Clock` as Clock input, and enable
   Follow Logic clock. Keep the controller selection separate from this timing input.
4. Set the quarter-note beats per bar to match the project (4 for ordinary 4/4).
   MIDI clock does not convey time signature; compound meters require manual setup.
5. Start Logic from its beginning. Wait for the clock BPM display to lock (at least
   24 intervals), then choose 1, 2, 4 or 8 beats of capture. Lengths over eight seconds
   are rejected. Capture schedules for a future bar; it automatically finishes at the
   selected length. Stop cancels a musical capture; Capture does not shorten it.
6. Bring in schedules a prepared response for a future bar with at least 150 ms lead.
   Both capture and playback use Apple's device timeline scheduling. Recorded tails
   within 100 ms are trimmed/padded to the exact target sample length; larger deviations
   fail visibly. Nothing is inserted into Logic's Live Loops grid.

**Limits:** fixed tempo only, experimental timing. A missing clock for 0.5 seconds,
transport/position change, detected timestamp discontinuity, or >1% tempo change
stops synchronized work. A transport stop does not stop a manually launched free loop.
There is no continuous time-stretch/drift correction, no MIDI-clock offset calibration,
and no plug-in delay compensation in this app. The old loop's stop at replacement is
serviced by a 20 ms UI timer, so a brief overlap is possible (longer under UI stalls).
Do not claim sample-accurate replacement. Test against an audible Logic click for the
full 15 minutes; if drift or overlap is audible, keep free one-shot responses for QA
and do not treat synchronized looping as stage-ready.

### Musical context and analysis

The worker now computes energy-rise onset estimates and up to eight monophonic
pitch hints using bounded autocorrelation. They are DSP estimates, not neural listening,
transcription, reliable chord detection or inferred key. Chords, breathy vocals and noise
can mislead the pitch estimate. A user-supplied key is direction, not a detected fact.

Section, supplied key and artistic direction are sent with a phrase. Only the last four
**accepted decisions** enter a small, RAM-only musical history. Auditioned/discarded
candidates do not. The planner sees their slice orders and pitch-class summaries, with
personal memory recall still off. Clear musical history starts a new musical context;
restarting the bridge clears it too. No audio is stored in this history. Acceptance is
recorded when the backend acknowledges the choice, so a later playback failure can
still leave that chosen decision in history; retry does not duplicate it.

The output vocabulary remains source-slice gain/reordering/reversal and AUGMENT's
delayed layer. Pitch hints inform decisions but do not add pitch shifting or harmony
synthesis. Deterministic mode does not invoke the language model or use this history
for learned decisions. The 8-second model deadline still does not cancel an already
running inference inside the core; avoid repeatedly retrying a busy model.

### Required Mac QA before using sync in a performance

- Test dry guitar and voice channels individually; permission denial and recorder failure.
- Start a response loop, then test replacing it with the bridge down, restarting the bridge,
  repeated audition/accept, and Stop during download and queued launch. Preserve old audio
  on failed replacement; no late response may start after Stop.
- Confirm audition stays silent until acknowledged; verify the actual destination audibly.
- Save an unheard response, reopen the WAV in Logic, then save after stopping an accepted loop.
- Use the controller while Logic receives its own notes. Test repeated presses, unplug/replug,
  and channel selection. Avoid double-binding controller notes to unwanted Logic actions.
- With IAC: test start at zero, nonzero start, Continue, cycle jumps, stop, clock loss, tempo
  change, cancellation of queued capture/launch, and 15 minutes of click alignment. Test
  44.1 kHz and 48 kHz Logic/interface configurations; the companion requests 48 kHz capture.
- Capture monophonic held notes and chords; compare pitch hints in GET /v1/live with what
  was played. The feature is allowed to be uncertain; musical listening remains decisive.
- First run without Qwen, then with the existing Qwen instance. Watch Activity Monitor's
  memory pressure and Logic's CPU meter. One worker/candidate, one accepted loop and
  bounded descriptors do not guarantee safety from system-wide memory pressure on 8 GB.
  Stop the model if Logic glitches; do not download another model for these tests.

References:
- https://support.apple.com/en-us/102005
- https://support.apple.com/guide/audio-midi-setup/ams1013/mac
- https://developer.apple.com/documentation/avfaudio/avaudioplayer/play(attime:)
- https://developer.apple.com/documentation/avfaudio/avaudiorecorder/record(attime:forduration:)

## Local looping first

The local-looper update supersedes the earlier capture-waits-for-response workflow.
Read [Local looper with background AI](local-looper.md) for original-loop playback,
overdub/undo controls, expanded MIDI mapping, and the first-repeat timing limitation.
