# Futureproof, October 29: SUZY//AI cover-led 15-minute set

Status: rehearsal proposal and QA gates, **not** a completed Logic project.
The goal is a human-led set opening with Radiohead's "Pyramid Song",
passing through the original Appliance Latent Space improvisation, and
closing with "Weird Fishes/Arpeggi". One Google MRT2 Small model, 48 kHz
Logic project, no unnecessary second model on the 8 GB show Mac.

## Runtime ownership

- **Piano and arpeggio:** deterministic Logic MIDI/Live Loops instruments.
- **Harmony steering:** playable or prepared MIDI regions on Google's official
  MRT2 Small AU instrument track. The model is a responsive accompanist,
  not the owner of tempo, chord change, song form, or recognizable riffs.
- **AI audio effects/capture:** optional SUZY Toast AU as the Audio FX insert
  after MRT2. Its native AUDIO LOOP is memory-only and begins capture
  on the next audio block, **not** the next Logic bar.
- **Vocals:** mic → BOSS VE-22 → Scarlett input → a separate Logic mono
  audio track. Voice remains usable when AI is muted, and there is no
  demonstrated live mic-to-MRT2 conditioning connection.
- **Prepared beat/synths:** separate Logic tracks, one authoritative
  clock and click, with AI prints kept as backup.

The MIDI browser at port 7345 does not drive neural audio, native AU
parameters, or Logic Loop cells. Avoid depending on it for the show.

## Proposed cue sheet

| Time | Musical scene | Deterministic arrangement | AI job |
| --- | --- | --- | --- |
| 0:00–2:45 | PYRAMID / FLOAT | Opening piano and live voice | Initially silent, then very soft held chord response |
| 2:45–3:40 | Bridge | Gmaj7/A6 tones move toward Em7; original improvised transition | Print or softly loop an ambient response only if proven |
| 3:40–9:45 | APPLIANCE / EVOLVE | Original beat, synth and vocals, Logic owns form | Generated counterline, textures and deliberate captures |
| 9:45–14:40 | FISHES / CURRENT | Fixed repeating arpeggios and 4/4 drums, live vocals | Restrained harmonies/texture, not the famous layered riff |
| 14:40–15:00 | End | Arranged final held tone and controlled fade | Logic AI mute/silence |

This implies **abridged/adapted covers**, not both original full-length
recordings plus a middle composition in 15 minutes.

### PYRAMID / FLOAT

The opening piano accent cycle has a recognized 3–3–4–3–3 group of
eighth notes (one reading places it across two bars of 4/4). Harmony
includes F# / Gmaj7 / A6. Keep the exact rhythm in a Logic piano MIDI
region or perform it yourself, not in stochastic MRT2 audio.
Earlier 105 BPM MIDI was a simplified **practice** clip, not a complete
cover or guaranteed original tempo.

Optional MANUALLY AUDITIONED Magenta style idea (not implemented as an
automated SUZY scene): "Sparse bowed-string and glass-harmonic
instrumental haze, slowly breathing texture, few attacks, wide silences,
no obvious drum beat". No negative prompt is guaranteed.

### APPLIANCE / EVOLVE

Own prepared groove, independent synth line and vocal phrasing; the
model can make genuinely generated responses when supplied note
conditioning. Optional style idea: "Warm, spacious jazz-rap and
neo-soul-informed pulse, deep round bass, restrained irregular
percussion, sparse electric keys, room for a live singer."

If SUZY Toast passes live QA, RECORD an AI response and lower AI LIVE
while keeping LOOP MIX above zero. This is one volatile loop with
destructive overdub and no undo or Logic-transport synchronization.
Print any essential result into Logic.

### FISHES / CURRENT

The recording is commonly transcribed near 153 BPM, 4/4; the feeling
comes from repeating 3-against-4 guitar/arpeggio figures. A useful
harmony map for a simplified cover is Em7 / F#m7 / A / Gmaj7.
Use deterministic Logic arpeggiator/synth regions for the interlocking
patterns, a real quantized beat and a live vocal.

Optional manually auditioned Magenta style idea: "Translucent
picked-string shimmer and soft upper harmonics, minimal ensemble,
long airy tails, unobtrusive bass, space for fast repeating patterns."
If AI fights the riff, mute its Logic track. At 153 BPM, four 4/4 bars
last ~6.27 seconds, but SUZY Toast REC is **not bar-quantized**, so
do not use a hand-started loop as the timekeeper.

## Five hard QA gates for actual Thursday use

1. **AU installed/validated in Logic on the actual Mac.** CI builds
   successfully, which alone does not prove Logic Plugin Manager,
   Audio Unit validation or sound.
2. **Hear Magenta through the toaster and RECORD a generated phrase.**
   Lower AI LIVE to 0; ensure the captured AI loop stays audible.
   STOP, PLAY and CLEAR must work.
3. **Independent vocal path.** Mic → VE-22 → Scarlett → Logic vocal channel
   remains audible while the AI channel is muted. Confirm monitoring
   does not double or feed back.
4. **Durable printed audio.** Print a useful AI passage in Logic, save,
   quit, reopen, listen. The native looper's internal audio is NOT
   saved within the Logic project.
5. **Offline 15-minute stress rehearsal**, full set, 48 kHz, low load
   with just MRT2 Small. Watch CPU/memory pressure/audio dropouts.
   Keep a no-toaster Logic backup.

Decision: if any QA gate fails, **do not use the new SUZY Toast AU live**.
Keep Google MRT2 Small if proven stable; use Logic printed/quantized
AI clips or a completely AI-muted cover fallback.

## Post-show coding priorities

- Logic-hosted bar-boundary quantized audio capture and recording state.
- True loop Undo, durable WAV export and host transport/tempo change handling.
- Song scenes for style/MIDI conditioning, **only after** validated
  Google AU integration; otherwise use native C++ magentart core
  in a later separate standalone host.
- Optional separately routed voice analysis, without claiming
  that audio style prompting is continuous microphone listening.

## References

- Magenta MRT2 official capabilities and 48k:
  https://magenta.withgoogle.com/mrt2
- MRT2 model architecture and Small streaming:
  https://magenta.withgoogle.com/magenta-realtime-2
- Logic quantized Live Loops:
  https://support.apple.com/guide/logicpro/start-and-stop-cells-lgcpb461e752/10.7/mac/11.0
- Pyramid rhythm analysis:
  https://www.mtosmt.org/issues/mto.13.19.1/mto.13.19.1.hesselink.php
- Pyramid harmony:
  https://reverbmachine.com/blog/radiohead-chord-theory/
- Weird Fishes multi-arpeggio:
  https://guitar.com/features/radioheads-10-greatest-guitar-moments-ranked/
- Weird Fishes rhythm and BPM:
  https://supersimpledrum.com/songs/weird-fishes-arpeggi-radiohead
