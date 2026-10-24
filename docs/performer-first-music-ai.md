# Performer-first SUZY//AI: rethink the instrument, not just the prompt

**Status:** architecture and UX decision memo, October 24, 2026.
The user is presently on a different computer, so this PR is suitable for
source-code review and design decisions, **not Focusrite hardware QA**.
Futureproof is scheduled October 29. Do not endanger the prepared Logic show.

## What was wrong with the old interface?

The prior panel looked like an audio-driver QA form:
1. Choose device; choose channel; choose output; test.
2. Set BPM, beats, chord, count down and a long *genre instruction*.
3. Press Capture, wait for a text model to create at most 8 monophonic notes.
4. Hear a plain sine tone, in isolation, with no Logic clock/audio bus.

The musician had to be a sound engineer, conductor, and test operator just
to hear an uncertain musical reply. That is the wrong *stage mental model*.
A real performer needs an instrument with obvious actions, tactile
shortcuts, instantaneous silence, and an AI contribution that can enter
the prepared song without ruining it.

This redesign moves technical routing to **Audio setup** and moves code
and source IDs to **Diagnostics**. The visible page focuses on three
distinct prompts to the EXISTING local composer, not fake new audio
engines: SPACE, ANSWER and COUNTERLINE. Big buttons, keyboard shortcuts
1/2/3 (role), Space (capture), Enter (audition), Esc (STOP).
The backend and safe limits are unchanged: still phrase turns, no
Logic bus input, no actual beat clock, one monophonic sine-synth answer.

## Why Grimes is a better workflow reference than another AI dashboard

Grimes described Juno-G + SP-404 + separate vocal processing and looping,
with prepared backing and her own samples, in a firsthand interview:
https://www.tinymixtapes.com/features/grimes
In 2016 she described two SP-404 samplers and separate vocal looper/pedal
roles: https://www.ableton.com/en/blog/grimes-bird-calls-and-dentists-drills/
A later interview discusses moving away from doing every live loop during
large shows and triggering prepared music intentionally:
https://preposterousuniverse.com/podcast/2019/11/18/73-grimes-c-on-music-creativity-and-digital-personae/

**Our translation (not claiming Grimes uses AI):**
- **Logic** is the timekeeper: prepared beats, synths, live loops.
- **VE-22** is the vocal performance device: immediate vocal effects.
- **AI instrument** is one separately controllable layer: alternate,
  audition, blend, mute, never auto-replace the live musician.
- **SUZY//AI** is the local musician-owned interface, knowledge and
  evaluation; no keyboard typing while performing.

## The most important new model to investigate

Google launched **Magenta RealTime 2** in June 2026: a purpose-built
streaming MUSIC/AUDIO model, not a text LLM being asked to write JSON notes.
It offers a 230M-parameter Small model claimed to stream in realtime on
any Apple Silicon Mac, including Air; a 2.4B Base model requires a much
faster Pro/Max machine. It provides a prebuilt AUv3 instrument and
standalone **Jam** and **Collider** apps with MIDI steering and prompts.

Primary official sources:
- https://magenta.tensorflow.org/magenta-realtime-2
- https://magenta.withgoogle.com/mrt2
- https://magenta.github.io/magenta-realtime/models.html
- https://huggingface.co/google/magenta-realtime-2

Its weights are CC BY 4.0, code Apache 2.0, with responsible-use terms;
check attribution and output clearance. The download docs specify around
450 MB Small model and 48 kHz stereo output. The model is primarily
trained on instrumental stock music and must **not** be advertised as an
Illmatic/Badu/Cash Crop style-cloning system.

**Critical caution:** "works on any Apple Silicon Mac" does NOT prove
small-model memory/thermal safety while Logic, Reaper, Qwen, Scarlett
and background agents all run on an 8 GB laptop. Test the bundled
standalone **Jam app FIRST**, with Logic closed and Qwen turned off.
Next test the AUv3 instrument in Logic at 48 kHz with ordinary MIDI.
Record CPU/memory pressure, audible dropouts and startup/offline use.
Only then consider composition with Logic and SUZY//AI.

MRT2 controls generated audio via MIDI and text/audio *style prompts*.
A prior audio sample is not automatically a continuous *microphone
listener*, and published project work discusses future audio-streaming
input. Do not promise that MRT2 already listens to Suzy's full voice
and Logic beat simultaneously. For initial tests, steer with *Suzy's
MIDI controller*, and keep Logic as the backing source.

## Proposed instrument architecture

```text
PREPARED LOGIC BEATS / LIVE LOOPS       --> MAIN OUTPUT (independent)
LIVE MIC --> VE-22 --> SCARLETT         --> VOICE (independent)
MIDI CONTROLLER --> LOGIC AI TRACK     --> MAGENTA MRT2 SMALL AUv3
            or standalone Jam first       |  generated music audio
                                          v
                                   MIX / MUTE in Logic

SUZY//AI research / Qwen optional --> rehearsal notes + musical directions
NOT AN AUDIO-THREAD DEPENDENCY; shut down on an 8GB machine if needed.
```

## Why not simply replace Qwen with a larger LLM?

A bigger language model can be a better *director*, but is not
automatically a better low-latency MIDI/audio musician. Repeated vague
jazz-rap background citations cannot supply performance timing, chords,
drum interaction, or original arrangement decisions. On 8 GB,
upgrading a 1.7B LLM risks higher latency and memory contention.
Prioritize **modality and control**, not parameter count.

## Product decisions, in order

1. **Now / from any computer:** design the control surface, research the
   Magenta dependencies and rights, review PRs, and add tests. No way to
   prove local Mac device routing from another physical computer.
2. **First Mac rehearsal:** test the existing panel's direct microphone
   input and Qwen response, BUT also install Magenta Jam Small and
   assess whether generated musical audio is actually inspiring.
   Do not run both models together at first.
3. **If Magenta Small passes:** use its AUv3 plugin on one Logic software
   instrument track, driven by the Keystation. Logic's fader or mute
   becomes an immediate kill switch. Keep vocals/VE-22 independent.
4. **If Magenta Small fails:** keep the proven Logic sound, and let Qwen
   propose MIDI offline/noncritically for subsequent loops; not an
   always-on mandatory stage dependency.
5. **After Futureproof:** build a real time-aligned Logic MIDI/beat bridge,
   and a human preference / original-musical-examples dataset. Validate
   what "90s groove" actually sounds like with the musician, rather
   than promoting artist-name prompts.

The single hard truth: a three-prompt panel cannot turn Qwen3 into a
skilled musician. A local **music-native** model and an artist-owned
gesture interface are more promising, but must be auditioned, not
declared successful in advance.
