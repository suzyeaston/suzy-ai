# SUZY//AI / TONIGHT: playable local AI musicians, not another Qwen prompt
Updated October 24, 2026. Target hardware: Apple Silicon Mac, **8 GB RAM**,
macOS 14.6.2, Scarlett Solo, Boss VE-22, Keystation MIDI, Logic Pro.

## Research decision

The most important architecture distinction: SUZY//AI's local Qwen3 1.7B
is a **text model**. Source-backed Illmatic / Baduizm / Rascalz research
makes better musical *directions*, not an audio-native *performer*.
Asking Qwen to emit 2-8 JSON MIDI events over an unobserved Logic beat is
not equivalent to an improvising live R&B musician.

For real musical audio TONIGHT, start with an already-built model.
Only implement code for the gap between YOUR voice / MIDI and that model.

## Shortlist of free / open-source creators and implementation value

| Project and primary source | Who built it / actual engine | Local real-time role | Practical tonight? | Limits |
| --- | --- | --- | --- | --- |
| [Google Magenta RealTime 2](https://github.com/magenta/magenta-realtime) / [prebuilt apps](https://magenta.withgoogle.com/mrt2) | Magenta team; on-device 230M *Small*, MLX/C++ engine, AUv3 and Jam/Collider | **Generates musical audio** from MIDI steering and text/audio-style prompts | **YES, first test**: 450MB Small download and Jam app or Logic AUv3 | No verified continuous raw mic / DAW-bus listening; 48kHz; model trained mostly instrumental stock music; no guarantee of 90s-hip-hop/R&B feel |
| [Neutone SDK](https://github.com/Neutone/neutone_sdk) / [free FX plugin](https://neutone.jp/fx) | Nao Tokui + Neutone contributors; LGPL-2.1 SDK, free AU/VST model host | **Turns live recorded audio** into neural textures/effects using compatible local models | **YES, alternative**: install Neutone FX on one vocal or audio track | Effect/timbre change is NOT original second vocalist or intelligent call/response; model CPU use varies; 8GB minimum recommended |
| [IRCAM RAVE](https://github.com/acids-ircam/rave) / [RAVE plugin](https://forum.ircam.fr/projects/detail/rave/) | Antoine Caillon, Philippe Esling / IRCAM ACIDS | Fast neural timbre transfer and new sounds in VST, standalone ecosystem | **OPTIONAL**: existing preset and plugin, not full training | Training from your own original stems is a longer project, not tonight's path |
| [Google DDSP-VST](https://github.com/magenta/ddsp-vst) | Magenta / Jesse Engel and contributors | Neural instrument morphing, AU/VST, MIDI-playable synthesis | **OPTIONAL**: sample-to-neural instrument and vocal/timbre experiment | Not accompaniment composition or live rhythm awareness |
| [Surge XT](https://github.com/surge-synthesizer/surge) | Surge Synth Team | Real, expressive FREE AU synth played by conventional MIDI, good sounding Qwen/MIDI renderer | **YES, sound fallback** | A synthesizer, **not AI**. Must not claim it composed the melody |
| [Sonic Pi](https://sonic-pi.net/) | Sam Aaron + community | Free live-coded, sequenced music performance and OSC/MIDI bridge | YES for predictable beat experiments | Algorithmic patterns are NOT necessarily neural AI |

**Not the priority for tonight:** MusicGen full-track prompting,
heavy 2.4B Magenta Base, RAVE training, LLM fine-tuning,
browser-cloud Lyria services, paid Max/MSP, or large Python/JAX installs.
The easy win is *play a downloaded AU with a MIDI keyboard*.

### Why MRT2 Small is the priority

Official Mac app page:
https://magenta.withgoogle.com/mrt2

Published hardware table:
https://magenta.github.io/magenta-realtime/models.html

- Small is 230M parameters and reported to run in real time on any
  Apple Silicon MacBook. **8GB Mac running Logic concurrently is NOT
  independently benchmarked**. The base 2.4B model is not suitable here.
- Native AUv3 and standalone apps ship as downloadable builds.
- **Magenta Jam** is a quick, interactive MIDI-steered musical-audio model;
  no requirement to fork/build code or run Qwen in the same session.
- The first launch downloads the model weights, ~450 MB Small.
- The engine outputs 48kHz stereo audio: set Logic's project/audio
  sample rate to 48kHz if using AUv3.
- The MIDI-steered ensemble follows playing/harmony, but isn't trained
  specifically on the copyrighted albums we're researching. Use creative
  descriptions of original pocket/texture, not artist impersonation.
- Source code Apache 2.0, model weights CC BY 4.0, attribution required
  where applicable; model card says Google claims no output rights and
  prohibits infringing content:
  https://github.com/magenta/magenta-realtime/blob/main/MODEL.md
- The model's public docs discuss expanded audio-stream inputs as
  future work. **Audio style conditioning ≠ live Scarlett audio listening.**

## PLAY TONIGHT: a staged test, not an installation marathon

**Trial 1: real neural music from the Keystation (best chance of success)**

1. On your Mac (not this different computer), close/stop SUZY//AI Qwen
   and other heavy background AI. Open
   https://magenta.withgoogle.com/mrt2 and download the macOS app bundle.
   It is free and the source is public. Install **Jam**.
2. Use wired/headphone output, at low volume. In macOS
   Audio MIDI Setup set audio interface/output to **48,000 Hz**.
   Run Jam and choose **mrt2_small**, not the 2.4B base if given a choice.
   First launch may fetch a ~450MB checkpoint. Do not start performing
   until the download completes.
3. Connect the Keystation Mini; select/enable its MIDI input in Jam.
   Start with one sustained minor chord and vary a single note. Notice
   whether the generated musical texture responds. Play in **silence
   first**, without Logic competing for the same 8GB machine.
4. If the audio is pleasant and CPU/memory pressure stable, stop Jam,
   install the bundled **MRT2 (AU)** plugin:
   https://github.com/magenta/magenta-realtime/blob/main/examples/mrt2/auv3/INSTALL.md
   Move plugin-host app to its final /Applications location FIRST,
   then launch once to register AUv3, restart/rescan Logic.
   Select a new **software instrument** track and choose Google/MRT2.
   Set project to 48kHz before enabling. Feed the Keystation MIDI track.
5. Place this AI track UNDER your own 90s Logic beat, start very quiet,
   and use Logic's track mute as an independent hard kill switch.
   Listen for a contrasting texture that isn't crowding your vocal.
   If you get glitches, disable the AU; your prepared backing continues.

**Trial 2: actually use your voice to steer a neural music model (optional experimental code)**

SUZY//AI now contains `suzy_ai.music.voice_midi_bridge`, an *OPTIONAL*
**dry monophonic pitch-to-CoreMIDI** converter. It is **not an AI model**.
Magenta generates the AI's audio AFTER receiving the corresponding MIDI.
There is no export, no Qwen prompt, no cloud and no model inference in
our audio callback.

Install ONLY when back at the Mac and after you have established that
MRT2 works on its own:

```bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m pip install -e ".[live-midi]"

# Show CURRENT input and MIDI output numbers; these change on reconnect:
.venv-mac/bin/python -m suzy_ai.music.voice_midi_bridge --list-devices

# If using standalone MRT2.app and it advertises virtual
# CoreMIDI port "Magenta RT Input", then:
.venv-mac/bin/python -m suzy_ai.music.voice_midi_bridge \
  --input-device "Scarlett Solo USB" --input-channel 1 \
  --midi-output "Magenta RT Input" \
  --transpose 0
```

If the name differs, use the actual output name/index from `--list-devices`.
Never guess an output index from this document. The documented **MRT2
standalone app**, which is different from Jam, creates a virtual port named
`Magenta RT Input`:
https://github.com/magenta/magenta-realtime/blob/main/docs/apps/standalone_app.md

For Logic AUv3, use a deliberately configured **IAC bus** as the
`--midi-output` only if Logic routes that input to the MRT2 instrument
track. Do not put the AI MIDI path back into its own input. Plugging
Scarlett mic into this Python bridge while Logic/another app is open
may create CoreAudio device contention; fall back to Keystation testing
first. Stop the Python bridge with **Ctrl+C**, which sends explicit
Note Off, All Notes Off and All Sound Off.

Known limitations of voice bridge: approximate **one note at a time**;
45ms window, ~80-170ms debounce plus audio/model latency, conservatively
silences on rest, no drum analysis or beat/bar grid, no VE-22 harmony
tracking, no AI vocals, no guarantee of stable duet. Dry mic first,
headphones required, MIDI notes only; the neural audio comes from MRT2.
This is a technology proof-of-concept, not a live show requirement.

## BC provincial election while you jam

Saturday **October 24, 2026** is B.C. provincial final voting day.
**Polls close at 8:00 p.m. Pacific** and preliminary results start at
https://results.elections.bc.ca/ according to Elections BC.
Live television coverage and projections are NOT the same as official
results. Avoid relying on estimates before 8 p.m.
Official source:
https://elections.bc.ca/news/final-voting-day-is-saturday-october-24/

## What should eventually become SUZY//AI?

One musician-owned interface with large physical/keyboard-mappable
controls: **CAPTURE, AI LISTENING, PROPOSE, AUDITION, ACCEPT, MUTE**.
Internally, keep 3 independent systems:
- Your Logic/VE-22 music stream (never interrupted).
- A music-native model (MRT2 or other local audio engine), MIDI
  controlled and mixed as a separate track.
- Optional Qwen 1.7B cultural/music *director*, only on a background
  low-priority process and only if the memory/latency budget permits.

Musical understanding still needs a future *measured beat/harmony path*
from Logic, and practice data from Suzy's accepted/rejected original
AI parts. A voice-to-MIDI bridge is a modest step; it does not solve
listening, phrasing intelligence, or jazz harmony by itself.

## Acceptance gates for tonight

- [ ] Magenta Jam Small plays real generated audio from Keystation.
- [ ] Audio output and 48kHz verified; no runaway volume/feedback.
- [ ] Generated music changes audibly with MIDI chords.
- [ ] Test at least one sparse, one active texture with your own beat.
- [ ] Logic backing keeps playing during immediate **AI track mute**.
- [ ] On the 8GB Mac, CPU/memory pressure and audio dropouts acceptable.
- [ ] Only if Jam/plugin passed: voice-to-MIDI bridge sends a note to a
      known CoreMIDI destination and releases all notes on silence/Ctrl-C.
- [ ] Record failure notes, don't silently label it "working".

**No live-hardware tests were run from this remote computer.**
