# SUZY//TOAST · live performance mode (October 29)

This is the **native plugin's built-in set**. There is no need to
download a MIDI backing track as a way of operating the toaster. The
toaster is a real Audio Unit **effect** attached to the Google MRT2
Small instrument in Logic. The plugin is not itself an instrument,
song arranger, host, microphone input, or MIDI output device.

## One stage-facing window

| Button | Real action inside Logic's inserted toaster AU |
| --- | --- |
| 01 · PYRAMID | Recall quiet/soft AI audio tone and mix, manual loop BPM reference 105; display Pyramid Song chord cues F# / Gmaj7 / A6 / Gmaj7 / F# |
| 02 · EVOLVE | Recall warmer/more present AI mix; display original-middle chord cues Em7 / A6 / Gmaj7 / F#m7 / Em7 |
| 03 · FISHES | Recall restrained, shimmering AI tone/mix; display Weird Fishes chord cues Em7 / F#m7 / A / Gmaj7 |
| PREV/NEXT CUE | Advance a **visible rehearsal cue only**; no MIDI, no transport, no Magenta chord change is claimed |
| RECORD, PLAY, OVERDUB, STOP, CLEAR | Control the **actual incoming neural audio** loop, in RAM |
| AI LIVE / LOOP MIX | Fade live Magenta audio independently of the captured phrase |
| SPACE · MUTE | Fade audio leaving this toaster AU, not the VE-22 vocal track or the entire Logic master |

**During the show, you press the notes/chords yourself on the
Keystation.** That's the real MIDI path into Google's MRT2 AU. The chord
labels remind you where the composition is, but neither the toaster
Audio FX nor PREV/NEXT CUE produces new MIDI notes.

### Tempo and timing

The toaster now **reads Logic's current reported BPM** when available
and uses it to determine the duration of new loop captures. Otherwise
it falls back to the selected scene's **manual** BPM reference.
Scenes **do not change Logic project tempo**, change Logic cell scenes,
or quantize RECORD to the next bar.

The native looper has one stereo phrase, destructive overdub,
no undo, no saved audio in a reopened project, and a bounded maximum
duration. For accurately synchronized passages use Logic Live Loops
cells or print the AI audio to a standard audio track.

### Vocal independence

Mic → BOSS VE-22 → Scarlett input → **Logic vocal audio track**;
prepared piano/arps/beats on their own Logic channels. The toaster
is added only after **the one working Google MRT2 AU** on its own
instrument channel, not on the master output. A stage-scene change
must not interrupt the vocal chain, alter Scarlett routing, reset
Logic transport, or destroy an active toaster loop.

### AI style caveat

Each scene has a **visible optional style reminder**. It does NOT
send prompts/PCA settings to Google's AU: official MRT2 model/style
parameters are not connected to this external Audio FX via the
native host's public interface. Presets recall real *post-model*
tone/saturation/AI-vs-loop levels.

An eventual MIDI FX/audio host companion or a custom MRT2-core
host could send proper model controls, but would need its own test and
cannot be represented as working at the Futureproof show.

### First full-system listening checklist

- [ ] Native AU loads as Audio FX **after** Google's MRT2 Small in a
      **duplicate** Logic session, on the actual 8 GB Apple Silicon Mac
- [ ] Physical Keystation plays Google's MIDI-conditioned AI while the
      performer sings through VE-22 and Scarlett independently
- [ ] Each big scene button alters the AI audio's post-effect
      character and levels but never changes/mutes the vocals
- [ ] REC captures genuinely generated audio and loops it after live
      AI is lowered; no runaway feedback or excessive clipping
- [ ] Logic host tempo shown in stage view matches the actual project;
      recording begins on press rather than on an exact bar boundary
- [ ] Logic audio track mute remains an authoritative safety kill,
      including if the toaster AU is bypassed
- [ ] Print important AI phrases, save the Logic project, close,
      reopen and prove the printed material still exists
- [ ] Run the uninterrupted 15-minute set fully offline and observe
      real CPU pressure/latency with headphones and mic

Any failure means **keep the existing Google MRT2 + Logic backing**
and omit experimental toaster from Thursday's stage project.

### Technical

The three stage definitions are plain C++ in
`Source/PerformanceScenes.h`; the Logic AU source recalls actual
`AudioProcessorValueTreeState` audio parameters on the UI thread.
The performance scene choice is saved as a Logic plugin parameter.
Master gain, SPACE/mute state, current loop audio and LoopBuffer
transport remain unchanged by scene switching.

GitHub Actions compiles the native Audio Unit and separately validates
these scene descriptors; still requires physical Logic QA.
