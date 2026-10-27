# Futureproof 2026 | October 27 Logic-first recording handoff

**Mode: performance rehearsal, not another model experiment.**

The earlier Qwen note composer generated only sparse short-note responses in testing.
The `suzy-ai` README records **audibly confirmed** Google MRT2 Small AU in
Logic Pro on Suzy's Apple Silicon 8 GB Mac; physical Keystation to model
worked with the Scarlett headphones and a 48 kHz Logic project. That is our
musical fallback. **Do not put Qwen/Python/virtual MIDI between the keyboard
and the known-good instrument on October 29.**

## Music and timing

A self-contained Standard MIDI File format-1 rehearsal arrangement was generated
and offline-tested on October 27 and delivered to the performer in the
ChatGPT rehearsal kit. Its source and supporting checker are in that kit;
it does **not** claim to be an existing .logicx project or an audio render
from Logic. It is original companion material, not Radiohead audio,
transcribed vocal lines, or a guaranteed recording-accurate arrangement.

| Scene | Bars | BPM | Start | Duration | What performer controls |
|---|---:|---:|---:|---:|---|
| Pyramid / Float | 126 | 105 | 0:00 | 4:48 | Vocal, sparse asymmetric F#/Gmaj7/A6 piano |
| Transformation | 60 | 120 | 4:48 | 2:00 | E minor-centred sustained voice to three-against-four fragment pulse |
| Fishes / Current | 313 | 153 | 6:48 | 8:10.98 | Live vocal, Em7/F#m7/A/Gmaj7 interlocking synth arpeggios |
| **Manual end** | | | **14:58.98** | | Music and AI stop on performer cue |

**Scene markers and tempo changes are MIDI metadata.** In Logic use
`File > Open` on the full .mid as a **new project** to retain the global
tempo/marker tracks. `File > Import > MIDI File` into an existing project
is not equivalent and may not preserve those global properties.
Reference: https://support.apple.com/guide/logicpro/lgcpdf6a3851/mac

The opening is a study of five 3-3-4-3-3 eighth-note chord accents,
not a claim of exact performance transcription. The middle develops
original material. The closing arpeggios cross a 3-eighth cycle against
the Logic 4/4 beat. The full arrangement is optional behind real playing;
mute or edit any track that makes the arrangement too busy.

## Fastest path to *recorded sound*, before extra AU experiments

1. Scarlett headphones, Scarlett for both Logic input/output; 48 kHz,
   start 128 sample I/O buffer (try 256 if overload). Shut the standalone
   MRT2 Jam app and Qwen first to avoid two neural engines.
2. Open the **16-bar Pyramid MIDI clip as a new Logic project**.
   Solo the piano track, confirm actual sound. Add a separate software
   instrument track for live Keystation; don't route it through an
   experimental CoreMIDI bridge.
3. Dynamic mic -> VE-22 input -> VE-22 L/MONO XLR -> Scarlett XLR.
   Create a Logic mono audio track on the matching Scarlett input.
   Turn on **either** Scarlett Direct Monitor **or** Logic software
   monitoring, not both. Watch the input meter; record a 20-30 second
   voice-and-keyboard take. Confirm actual playback.
4. Open the full 15-minute MIDI in a new Logic project, choose suitable
   Logic instruments on the backing tracks, add the vocal track, save
   as a native .logicx and do a complete recording pass.
5. Add Google's *official* MRT2 Small AU on a **separate** Logic
   software instrument channel, initially played directly from the
   keyboard. Logic AI track **mute** is the reliable audible panic.
6. Only if the first four steps have been heard: insert experimental
   SUZY Toast as AUDIO FX **after MRT2**. Its native audio loop is RAM-only
   and recording is not aligned to Logic bars. Print the AI audio
   into a real Logic track, save, reopen and listen before using it
   as backing. If AU validation or audio output fails, bypass it.

## Test boundaries / dangerous illusions

- Existing `/toaster` browser stage at port 7345 sends MIDI. It cannot
  mute Google's **audio**, record vocals or automatically select Logic
  track inputs. This is not a panic control.
- SUZY Toast's scenes recall post-model tone and gain, not the
  Google neural latent-space or prompt parameters.
- The new standalone one-open Mac host, draft PR #65, **compiled on CI**,
  but is still **not physically auditioned or certified**. It cannot
  replace the proven Logic host on the strength of compilation.
- The BOSS VE-22 can be used for live vocal effects/loops, independent
  from the toaster's *AI-track* loop.
- One uninterrupted offline full-performance take on the actual Mac is
  the real passing test, not green unit tests.

## Performance safety

Voice, prepared piano and synth tracks stay audible if generated AI
fails; independently mute MRT2's Logic track. Keep the saved Logic MIDI
arrangement, recorded vocal takes, and bounced AI audio rather than
depending on volatile effect buffers or standalone app state.

**Today's objective: hear, record, rehearse.** 
