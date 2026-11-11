# 🍞 SUZY//TOAST Futureproof · one-open experimental Mac stage

**Goal:** Open **SUZY TOAST Futureproof.app**, hit **START STANDALONE**,
play the Keystation and sing. There should be **no Terminal, Git, Qwen,
Python, browser control surface, or Logic project** required for the
standalone *runtime*. The model is the official, **already-installed**
Google Magenta RealTime 2 Small Audio Unit, hosted directly by AVAudioEngine.
No second neural model runs on an 8 GB show Mac.

## What the one-download bundle contains

- Native Apple Silicon SwiftUI stage host for the already-installed
  MRT2 Small software instrument. Selects a physical MIDI source
  favoring "Keystation" by name; sends raw notes into MRT2. On-screen
  NEXT CHORD holds the appropriate MIDI harmony until changed.
- Real native SUZY Toast audio-effect **.component** bundled inside the
  app (JUCE AU compiled from this repo) to record and loop actual
  generated audio. The app copies it to the user Audio Units folder on
  first run; never touches Google's component. **Audio Unit discovery
  may require restarting the app after installation.**
- Original, locally synthesized loopable backing WAVs at 48 kHz,
  generated from code in this repo, for PYRAMID / EVOLVE / FISHES.
  They are *arrangement scaffolds*, not exact Radiohead transcriptions,
  original recordings, or finished backing productions.
- Scene buttons recall post-Magenta audio FX profiles and original
  backing WAVs; keyboard and on-screen cue changes send real chord MIDI.
  Mic monitoring is separate from the generated AI channel.

## One-host rule

| Mode | Intended job |
| --- | --- |
| **START STANDALONE** | Hosts a single MRT2 instrument, optional Toast AU, voice monitor and original section backing |
| **OPEN LOGIC** | Stops standalone engine *first*, opens existing Logic Pro. Does **not** silently create or edit a Logic project or install preset channel strips. Logic remains a separate trusted host. |

Do **not** run the standalone host *and* Google's MRT2 Logic instrument
simultaneously: 8 GB RAM is tight. Neither path needs Python, Qwen or Jam.

## Before performing

The one ZIP from GitHub Actions is an **experimental ad-hoc-signed**
Mac app, **not notarized** or Developer ID signed. It's an internal
test artifact, not a public polished release. Never disable macOS
Gatekeeper or overwrite Google's official AU to force a build to load.
The performer must decide whether they trust the build. Apple's standard
app-open checks/permission prompts may still appear.

As with all audio apps, plugging in the Keystation, Scarlett and mic is
physical. This code cannot remote-set Mac audio devices or grant mic
permission. It will request mic access **only if** ENABLE VOCAL INPUT is
clicked. The system-default input needs to be the VE-22/Scarlett; the
output needs to be a device you can hear. Verify monitoring to avoid
doubling with VE-22 direct monitoring.

The App's first launch copies its own AU effect to
`~/Library/Audio/Plug-Ins/Components/SUZY Toast.component` only if
missing. This copy does not modify an existing user AU. A first-launch
rescan might still be necessary on macOS.

## Truthful limitations

- Neither the app nor the JUCE Toast audio effect has direct write
  access to Google's neural model prompts or latent-space parameters.
  The stage app sends MIDI *upstream* into Magenta by hosting the
  instrument, while Toast loops audio *downstream*. This is the
  genuine data path.
- This is not a complete karaoke rendering of the two Radiohead
  songs. Musical verses, precise melodic voicings and sections are
  performed **live by the musician**, with original harmonic scaffolds
  playing.
- The standalone stage backing loops are basic synthesized sounds,
  with no arbitrary BPM quantization or scene crossfades, designed to
  be musically usable and low-CPU rather than imitatively produced.
- The Toast AU's loop is volatile, has destructive overdub, no undo,
  and is not currently locked to Logic/the backing WAV barline.
  Onscreen RECORD/STOP/PLAY buttons send exact-once AU parameter
  commands; validate on an actual Mac before trusting it onstage.
- Host-side mic input is a separate AVAudioEngine mixer, not a source
  for Google's Magenta neural generation or a Toast recording bus.
- Logic mode merely opens Logic; its routing/presets cannot be
  configured reliably by this app without a tested native project.

## Actual QA to pass before October 29

- [ ] Downloaded one-open .app launches (no codesign/crash errors).
- [ ] Finds official installed Google MRT2 Small AU and plays actual AI
      audio when physical Keystation MIDI or NEXT CHORD is sent.
- [ ] Internal synthesized PYRAMID/EVOLVE/FISHES accompaniment plays
      separately; section change does not leave a stuck MIDI note.
- [ ] Bundled SUZY Toast AU registered and can receive app's exact-once
      RECORD / PLAY / OVERDUB / STOP / CLEAR commands.
- [ ] Reduce AI LIVE to zero and keep LOOP up: hear independent captured
      neural phrase through speakers.
- [ ] VE-22 mic on the chosen system input, Scarlett output; no doubled
      monitoring or feedback; mic mute independent of AI/loops.
- [ ] Full 15-minute **offline** show rehearsal with all three scenes,
      no overload or dropouts on actual 8 GB Apple Silicon Mac.
- [ ] Hit STOP AUDIO; Logic project remains functional without this app.

If any fail, use the already-audible original **Logic + official Google
MRT2 Small AU** and prepared loops instead. The all-in-one app is
experimental until actually auditioned on performer hardware.

## Build

The repository workflow `futureproof-app.yml` generates the backing
using the Python **standard library** at compile time, builds the pinned
JUCE AU effect, compiles the native Apple Silicon host and signs/packages
the .app with its AU and three WAV files. Python is NOT needed at runtime.

**Licensing:** Magenta AU and model are *not* redistributed; the user
must already have Google's original software installed. JUCE AU binary
distribution requires compliance with its GPLv3/commercial license.
Keep this prototype as an internal test artifact until licensing and
signing are resolved.
