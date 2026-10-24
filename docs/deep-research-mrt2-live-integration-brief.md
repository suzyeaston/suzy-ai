# Deep Research assignment: implement SUZY//AI as a REAL local, playable AI music instrument

**Date:** 2026-10-24. **Priority:** actionable hardware/software integration and musical agency, not another catalog of music models.

## Situation and actual repo (read before researching alternatives)

Repo: https://github.com/suzyeaston/suzy-ai

**Already merged:**
- PR #33: `suzy_ai/music/era_knowledge.py`, cited 1990s genre histories.
- PR #36: Rascalz *Cash Crop* (1997) / Vancouver cultural research.
- PR #37: `suzy_ai/music/research_cards.py`, opt-in historical musical-action cards.
- PR #38: `suzy_ai/music/listening_lab.py`, exported-WAV comparison. **Not an acceptable live-performance UI.**
- PR #39: `suzy_ai/music/stage_panel.py` + `stage_panel.html`, localhost browser controls for Scarlett→Qwen→basic sine-note playback, no Logic audio input.
- PR #40: performer-first SPACE / ANSWER / COUNTERLINE interface.
- PR #41: `suzy_ai/music/voice_midi_bridge.py`, sounddevice + python-rtmidi, Scarlett mono pitch→physical/virtual CoreMIDI output; optional `[live-midi]` dependency.

**Important:** Qwen3 1.7B GGUF on local llama.cpp is a small TEXT model, currently asked to emit MIDI event JSON in a separate composer. It has NOT proven musically competent or low-latency in Logic, and the performer reported two sparse notes and no recognizable difference from knowledge cards. Do NOT propose “just use larger Qwen,” add genre text or another generic chat UI as the solution.

**Human artist:** Suzy, a professional musician, creates and plays original 1990s hip-hop/R&B inspired backing beats, keys/synths and vocals in Logic. References include Nas *Illmatic* (1994), Erykah Badu *Baduizm* (1997), A Tribe Called Quest, D'Angelo, Lauryn Hill, and VANCOUVER Rascalz *Cash Crop* (1997). The model should make ORIGINAL accompaniment and responds to Suzy, not copy particular artists' voices, samples or melodies.

**Equipment constraints:** one 8 GB Apple Silicon MacBook Pro, macOS 14.6.2; Logic Pro Live Loops, Focusrite Scarlett Solo, Boss VE-22 vocal pedal, dynamic mic, M-Audio Keystation Mini MIDI keyboard. Preserve the musician's audio if all AI processes crash. Futureproof performance is Oct 29, 2026 (15 minutes). No internet dependency at showtime, no paid API, no training on unlicensed commercial audio.

## Central research question

**What is the shortest, demonstrably working, completely LOCAL and FREE route from Suzy's Keystation and/or sung notes into a genuinely generative AI musical instrument, mixed and controlled INSIDE her existing Logic session, with immediate mute, while retaining the path to future true live listening?**

The deliverable is NOT a speculative list of models. It is a reproducible project-specific implementation architecture supported by upstream source code and a Mac QA script/scorecard.

## Start with THESE PRIMARY SOURCES (verify current code/release)

1. Official Magenta RealTime 2 product and architecture:
   - https://magenta.withgoogle.com/mrt2
   - https://magenta.tensorflow.org/magenta-realtime-2
   - https://github.com/magenta/magenta-realtime
   - https://github.com/magenta/magenta-realtime/blob/main/MODEL.md
   - https://github.com/magenta/magenta-realtime/blob/main/docs/models.md
2. Official Apple Silicon standalone MIDI routing:
   - https://github.com/magenta/magenta-realtime/blob/main/docs/apps/standalone_app.md
   - Confirm the app creates CoreMIDI input **Magenta RT Input**. Determine which **downloaded app** provides it; do NOT confuse developer-built standalone MRT2 with the separately packaged **Jam** demo.
3. Official AUv3 setup:
   - https://github.com/magenta/magenta-realtime/blob/main/examples/mrt2/auv3/INSTALL.md
   - Verify required **48,000 Hz**, permanent .app location BEFORE registering Audio Unit, plugin identity in Logic, available MIDI and continuous-controller behavior, audio output channel, and whether an IAC bridge is necessary.
4. Relevant Apple plugin-host compatibility:
   - https://support.apple.com/en-us/102082
5. SUZY//AI existing code paths:
   - `suzy_ai/music/voice_midi_bridge.py`
   - `suzy_ai/music/phrase.py`
   - `suzy_ai/music/stage_panel.py`
   - `suzy_ai/music/stage_panel.html`
   - `suzy_ai/music/qwen_composer.py`
   - `suzy_ai/music/listening_lab.py`
   - `tests/test_voice_midi_bridge.py`
   - `pyproject.toml`
   - `docs/open-source-live-ai-tonight.md`
6. Other real model/plugin implementations ONLY if they genuinely solve a stated missing function:
   - IRCAM RAVE: https://github.com/acids-ircam/rave
   - Neutone audio FX host: https://github.com/Neutone/neutone_sdk
   - DDSP VST: https://github.com/magenta/ddsp-vst
   - Surge XT: https://github.com/surge-synthesizer/surge (non-AI instrument fallback)
   - CoreMIDI, python-rtmidi, Audio MIDI Setup/IAC, Logic supported AU routing, and safe native/Swift options.

## Distinguish these FIVE functions, don't mix them up

1. **Vocal pitch/gesture sensing**: existing Python probe converts *dry monophonic* microphone audio to estimated MIDI Note On/Off. This is deterministic; no audio-native listening or voice harmony recognition. Does it survive VE-22 processing, pitch bends and silence?
2. **MIDI conditioning**: Magenta RealTime 2 Small takes NOTE STATE/MIDI inputs and produces STREAMING neural audio. It might react to notes/chords, but does not necessarily follow Suzy's bar-grid, hear her beat, sing original words or create a separately editable MIDI score. Show exact current supported inputs, plugin/standalone wiring and code symbols.
3. **Stylistic/harmonic context**: MRT2 supports text prompts or audio style references. Audio *style embedding* from a clip is NOT the same as full-duplex continuous microphone listening. Confirm how to select/update prompts live and whether a musician-owned original beat can be used as licensed style conditioning (without copying melody/sample).
4. **DAW synchronization and mixing**: Logic sets tempo, transport, tracks and effects. The generated neural AUDIO should enter on its own mutable/MUTEABLE track. Differentiate MIDI ONSET response from transport/bar syncing, which requires an explicit clock/host position path.
5. **Musical collaboration**: the AI must leave space for human voice, sometimes remain silent, provide a useful sound and allow accept/reject. Do not equate arbitrary notes or a citation ID with R&B or jazz-rap competence.

## Exact code audit demanded

Read actual `voice_midi_bridge.py` and evaluate:
- `RATE=48000`, `WINDOW≈45ms`, `HOP=2048` frames, `stable_frames=2`, `silent_frames=3` and buffering: estimate **end-to-end onsets/releases** including two-buffer accumulation, CoreAudio, model output and Logic audio buffers. Show calculations as *theoretical*, then require measurement. Do not assume latency under 200ms on our exact rig.
- It creates a bounded `Queue(maxsize=6)` for input chunks but `_pitch()` decimates samples without anti-alias filtering. Is pitch detection robust enough for singing with the VE-22, vibrato, octave errors, silence, voice + backing leakage? Recommend a low-dependency replacement or anti-aliased DSP approach and test plan.
- Current stream holds **one MIDI note at a time**, fixed velocity 65; Qwen stage panel is a different path. Should these be one interface or two; which one owns the audio hardware?
- On overload, dropping samples can leave a hanging note unless a watchdog forces Note Off. Check watchdog logic, Ctrl+C behavior AND abrupt process termination/device unplug, disconnection/reconnect, permission denial and app freeze.
- MIDI direction/naming: does standalone **Magenta RT Input** enumerate as destination of `python-rtmidi.MidiOut` on macOS? Check actual API semantics; prove with MIDI monitor before expecting neural audio.
- Test channel indexing, devices named generically, mixed sounddevice/Logic CoreAudio access and input/output ownership.
- Evaluate *whether* recent upstream plugin already exposes voice-control hooks or **current** raw microphone streaming; if not, explicitly state gap.

## Architecture comparison: pick a winner

Score these against musical value (40%), 8GB stability (25%), install friction (15%), control/fail safe (15%), license/privacy (5%):

A. **No new bridge:** Keystation → `mrt2_small` AUv3 inside Logic → separate generative audio track, muted until artist chooses. This is the **baseline** and should be tested FIRST.
B. **Standalone voice steering:** Scarlett dry mic → improved local pitch feature extractor → CoreMIDI `Magenta RT Input` → MRT2 standalone → monitor; Logic remains separate. Use this to verify the new PR #41 bridge in isolation.
C. **Logic-integrated voice steering:** Scarlett → SUZY//AI → IAC bus → Logic input to MRT2 AUv3 → mix within Logic. Verify routing and avoid MIDI feedback or repeated processing of mic output.
D. **Custom integration:** embed Magenta C++ inference engine or add AU parameter/OSC bridge to the local UI only **if** (A) and (C) have demonstrated value; estimate build effort and maintainability.
E. **Alternative actual AI instrument:** Neutone/RAVE or others, only if MRT2 Small cannot deliver usable accompaniment with acceptable resource consumption. Clarify that neural timbre transform is not generative second-voice composition.

Do NOT pick a winner solely from advertised latency or parameter count. Describe a Mac smoke test for each and reject pathways that break the prepared Logic show.

## Implementation questions requiring concrete evidence

- Which exact MRT2 (AU) UI actions load the Small model, choose MIDI input, enable text/audio style conditioning and set gain/volume? Are these state-controllable externally (AU parameters, MIDI CC, OSC)? If not, leave the control in Logic and do NOT invent a Web API.
- Does MRT2 AUv3 output a beat-synchronized musical part by default? Does MIDI clock affect output? Does a Logic arrangement with prepared hip-hop drums keep playing if the model reloads/crashes?
- Is Magenta Jam MIDI available without building from source? Which downloaded zip contains Jam, MRT2 Standalone and AU? Is `Magenta RT Input` provided by Jam or only MRT2 Standalone? Verify.
- How does Logic safely receive SUZY//AI external MIDI from IAC and direct it only to one audio instrument, not all armed tracks?
- What is the **actual RAM pressure** for model weights + decoder cache + host plugin + Logic on an 8GB Mac? The 450MB on-disk model size is NOT total process working-set RAM.
- What are free/license conditions for source, weights and performance outputs, attribution requirements and restrictions? Identify the producer-facing legal decision plainly.
- Can the local model create a meaningful R&B *answering instrument* while Suzy sings, versus continuously filling the sound with uncontrolled generative music? Define an audible acceptance rubric, not merely a valid-JSON test.
- Define the **minimum dependable controls**: AI ARM, MIDI FOLLOW, AI AUDIO MUTE/UNMUTE, NEXT IDEA, ALL NOTES OFF, STOP AI, audio channel LED and model status. Use simple MIDI mappings and physical mute priority.
- Which functions MUST run on real-time audio callback vs worker thread, and how to avoid resource contention and deadlocks?

## Experiment protocol for the artist, without exporting WAVs

Use a single **Suzy-owned original** 4- or 8-bar 1990s-inspired beat.
Do three audible trials, all with gain-limited AI:

**1. Keyboard-to-MRT2:** play a sustained chord, change one note, pause, then record whether generated AUDIO changes. Confirm AI track mute works independently of the beat. Qwen OFF.
**2. Mic-to-MIDI routing:** send dry mic pitch to known CoreMIDI port; check note-on/off via MIDI Monitor *before* loading MRT2. Vocal silence must not sustain a stuck note; kill all notes and close reliably.
**3. In-Logic accompaniment:** route verified MIDI to MRT2 AUv3, play the original loop, test SPACE/ANSWER/COUNTERLINE ideas as *controls of when notes reach the model*, not claim they are separate AI algorithms. Observe whether Magenta responds musically to vocal gaps.

Measure on actual hardware: 48kHz settings, model load time, memory pressure/swap, real measured note→audible-change latency, CPU spikes, PortAudio underruns, MIDI hanging notes, lost audio, crash recovery, output level and musician approval. Capture pass/fail and a sample-free timestamped log, not private audio exports. Compare Qwen-based counterline only AFTER the music-native path works.

**Go/no-go for October 29:** Suzy's prepared Logic beats and live vocal must ALWAYS continue if an AI fails. Any audio drops, sustained runaway MIDI notes, transport instability, unwanted recordings, or >1 missed transition excludes the experimental bridge from the show. For anything risky, keep Magenta/voice-MIDI for rehearsal only.

## Deliverables required from the deep research

1. An **executive recommendation** (max 250 words) and a table separating **works now / requires wiring / unsupported / uncertain**.
2. A **verifiable routing diagram** with note/audio direction and actual owned components, AND a separate diagram for future audio-aware AI.
3. A line-by-line **PR #41 architecture and bug review**, with filenames/functions/precise changes and tests to write.
4. A verified **MRT2 2026 API/installation audit** (app vs Jam vs AUv3, MIDI ports, 48kHz, weights/storage, CoreMIDI, model UI controls), backed by official current source code/docs.
5. A sequenced set of small proposed PRs, each with scope, exact files, acceptance tests, manual Mac test, rollback and dependency on prior PR. NO giant rewrite.
6. A **15-minute show-safe performance recipe** with simple input routing, a physical/logical mute and fallback that does not require a live model.
7. A musician-facing UI sketch with 3 to 5 large controls, no raw source JSON, and honest labels.
8. A quantified **8 GB Mac benchmark script/checklist** and a musical scorecard (timing, groove, harmony, space, response, control).
9. A rights/licensing appendix and distinct historical research sources; no artist-cloning instructions.
10. **Traceability:** mark each technical claim VERIFIED (with exact upstream link/code line), INFERRED, or NEEDS MAC TEST. Cite URLs and publication/update dates. Where code or docs contradict product marketing, report the contradiction.

**Success criterion:** An artist can boot her Logic set, steer an open-weights AI instrument using Keystation or original voice, hear meaningful generated musical audio, adjust/stop it immediately, and keep performing if the AI breaks. Don't confuse a prompt panel, MIDI note tracer or sine-wave preview for successful implementation.
