# 🍞 SUZY//TOAST native Audio Unit (experimental)

**Status: source prototype and CI candidate. Not yet listened to or validated in Logic.**
This is an **AU audio effect** after the working Google MRT2 Small instrument, not another
neural model, a MIDI effect, or a microphone router. Do not replace the proven
performance setup before October 29, 2026.

## The signal path

    Keystation → Logic MIDI track → Google MRT2 Small AU → SUZY Toast AU effect
                                                        ↓
                                 warmth, drive, live fade, stereo audio loop
                                                        ↓
                                                      Logic mixer → Scarlett output

    Mic → BOSS VE-22 → Scarlett input → separate Logic vocal track → Logic mixer
    Prepared beats / Logic Live Loops → Logic mixer

Scarlett input/output devices and microphone monitoring are selected in **Logic
Settings → Audio → Devices**, not in the toaster. This first AU captures only its
track's generated audio, not the VE-22 mic. The AI model doesn't automatically
listen to the singer or the full mix.

## Controls

| UI | Implemented function |
| --- | --- |
| BROWNING | Native soft low-pass filter |
| DESTRUCTION | Native mild saturation |
| AI LIVE | Independent live AI audio volume |
| LOOP MIX | Independent recorded-loop volume |
| MASTER | Master output gain |
| SPACE · MUTE | ~8 ms fade to silence of this AU's output; Logic track mute remains authoritative if bypassed |
| RECORD | Begin capture of AI audio for manual BPM × beats/bar × 1/2/4 bars |
| PLAY | Restart captured loop from its beginning |
| OVERDUB | Add a pass, destructively modifying the one in-memory loop |
| STOP | Stop loop, or cancel and discard partial recording |
| CLEAR | Remove loop |
| BPM / beats / bars | Manual duration controls; **not Logic transport sync** |

Loops are **temporary**: audio samples are not saved with plugin parameter
state. Print or record the output to a Logic audio track and reopen/listen.
The effect may reset loops on device/sample-rate reinitialization.

## CPU and memory budget

- No extra Magenta/Qwen process or network inference. This plugin is basic
  C++ DSP and a native vector interface, not React/WKWebView.
- A maximum **36 s × 48 kHz × 2 channels × 4 bytes = 13,824,000 bytes**
  (~13.2 MiB) of preallocated loop buffers per stereo instance.
- No allocation/file I/O/model inference in the render callback by design.
- Zero declared processing latency, though the host and MRT2 have their
  own latency; **actual CPU/dropout testing on the 8 GB Mac is required**.
- At 40 BPM, six beats per bar and four bars the capture fits exactly in
  the 36-second buffer. Longer requests fail visibly rather than overflow.
- Looping begins at the next processing callback when REC is pressed. This
  is a duration-based, free-running looper, **not sample-aligned to Logic
  bars** and not a complete multitrack looper. There is no overdub Undo yet.
- Keep Logic's original MRT2 channel and vocal chain independent. If this
  new AU fails, delete/bypass the insert and return to the known-good project.

## Source build and QA (do not attempt installation during Thursday preflight)

On the Mac with Xcode, CMake and Git:

~~~bash
cd ~/Projects/suzy-ai
git fetch origin
git switch feat/suzy-toast-native-au-effect

# JUCE-independent unit test:
c++ -std=c++17 -O2 -Wall -Wextra -Werror   plugins/suzy-toast/tests/loop_buffer_test.cpp -o /tmp/suzy-toast-loop
/tmp/suzy-toast-loop

# Mac Audio Unit build (downloads pinned JUCE 8.0.16-security once):
cmake -S plugins/suzy-toast -B build/suzy-toast -G Xcode   -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0
cmake --build build/suzy-toast --config Release --target SuzyToast_AU -j2
~~~

Successful JUCE COPY_PLUGIN_AFTER_BUILD copies the AU component to your user
Audio Units directory. Restart/rescan Logic and look under Audio FX, not the
instrument slot. The custom AU is a separate plugin: never overwrite Google's
MRT2 AU and always duplicate the Logic project before inserting it.

**Licensing:** JUCE is GPLv3/commercial dual-licensed. Before distributing the
compiled plugin, choose and verify a compatible licensing path. Nothing here
vendors JUCE source or Google's model weights.

## Proof still needed on actual performance Mac

- [ ] Xcode/JUCE source compiles for Apple Silicon.
- [ ] Audio Unit validation, Logic discovery and insertion as Audio FX.
- [ ] Keystation → working Google MRT2 → SUZY Toast → Scarlett audible.
- [ ] Mic → VE-22 → Scarlett → separate vocal channel remains independent.
- [ ] Record actual AI output; reduce AI LIVE; hear the retained loop;
      overdub, PLAY, STOP, CLEAR; validate SPACE and track mute.
- [ ] Listen to an independently printed AI audio region, save/quit/reopen.
- [ ] Offline cold start, full 15-minute stress test, no clicks/dropouts,
      memory-pressure spikes or accidental double monitoring.
- [ ] Pull the toaster insert and verify the original Logic-only show works.

## After the show: standalone SUZY//AI is possible

The preallocated LoopBuffer is ordinary C++ and can be shared with the
standalone app. A standalone **effect** alone cannot generate music: the
future host needs CoreAudio/MIDI routing, a native clock, file save/export,
and one embedded magentart::core MRT2 Small instance. It should not run
a second MRT2 engine alongside Logic on an 8 GB show machine.

The October 26 deep-research advice stands: keep the show simple, preserve
physical MIDI → Google MRT2 as a fallback, and gradually replace host
dependencies only when real sound, mute, capture and reliability have been
tested. Artist-owned sound identity is a later prompt-embedding/corpus step,
not a reason to double up on neural processes this week.
