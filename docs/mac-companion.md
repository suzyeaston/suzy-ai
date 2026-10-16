# SUZY // LIVE — first Mac companion

This is an experimental native Mac app for the EVOLVE WITH ME performance. It
captures dry audio from the **macOS default input**, sends it to the live-response
backend, and plays the returned source-audio response through the **macOS default
output**. Logic continues to own its Live Loops, instruments and transport.

This is not an Audio Unit. It does not read Logic buses/effects, insert a Live
Loops cell, or synchronize playback to Logic's bar clock. Bring in starts a loop
immediately. Expect manual timing and potential drift; quantized host integration
is the next milestone, not a claim of this PR.

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
reused and never killed. It does not start/download a model. For model mode use
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
has mode 0700. Accepted responses stay in memory only and are lost on app exit.

## Performance controls

- **Capture** starts a 2, 4, 6 or 7.5 second recording. Press again to finish early.
  Backend minimum is 0.25 seconds. The 7.5 second option leaves headroom below
  the backend's eight-second limit for recording-buffer timing.
- **Audition** plays the response once at the Response level setting.
- **Bring in / loop** accepts and loops it immediately, replacing the previously
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
in, Escape stop. Don't use these while editing tempo. MIDI works without app focus.

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
