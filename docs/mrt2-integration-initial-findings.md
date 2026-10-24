# Implementation findings: Magenta RealTime 2 Small + SUZY//AI + Logic
**Status: source and repo audit as of 2026-10-24; no Mac audio hardware was accessed.**

## Conclusion in one sentence

**Make Magenta RealTime 2 Small a separately muted Logic Audio Unit instrument, MIDI-steered by the Keystation first.** Only after that works should we route verified Scarlett voice pitches through PR #41's CoreMIDI bridge. Do not put Qwen or browser networking in the critical audio path.

## Verified current affordances (upstream)

| Capability | Source | What it ACTUALLY means |
| --- | --- | --- |
| Neural streaming musical audio | https://magenta.withgoogle.com/mrt2 | MRT2 is music-native; Qwen in our repo is not |
| Small 230M for any Apple Silicon Mac | https://github.com/magenta/magenta-realtime/blob/main/docs/models.md | Vendor compatibility, **not** tested 8GB multitasking or RAM budget |
| Official prebuilt Jam/standalone/AU apps | https://magenta.withgoogle.com/mrt2 | Play before building, start with the small model |
| MRT2 Standalone creates `Magenta RT Input` | https://github.com/magenta/magenta-realtime/blob/main/docs/apps/standalone_app.md | An actual CoreMIDI port target for python-rtmidi; **NOT a claim that Jam advertises the same port** |
| AUv3 registered by opening .app in final location | https://github.com/magenta/magenta-realtime/blob/main/examples/mrt2/auv3/INSTALL.md | Move `MRT2 (AU).app` into /Applications before first launch |
| Plugin/DAW audio must be **48,000 Hz** | same install document | Incorrect sample rate can cause silence or pitch distortion |
| MIDI conditions a pitch-state stream | https://github.com/magenta/magenta-realtime/blob/main/MODEL.md | Musical audio is generated from MIDI states, style and previous generated audio context |
| Published control latency approx **200ms** | https://magenta.tensorflow.org/magenta-realtime-2 | Engine-level figure, NOT measured Scarlett→Python→IAC→AU→Logic latency |
| Real-time audio streaming inputs described as future work | same release blog | Audio examples/style embedding are NOT continuous listening to Logic and live voice |
| Code Apache 2.0 / model weights CC BY 4.0 | model card above | Attribution and responsible-use conditions apply; Google claims no rights to generated output |
| Training mostly instrumental stock music | model card above | AI-vocal intelligible lyric/call-response or specific classic hip-hop feel NOT guaranteed |

## Existing SUZY//AI integration audited

```text
Original song (reliable):
 Keystation MIDI --> Logic Live Loops / instruments --> MAIN AUDIO
 Mic -> Boss VE-22 -> Scarlett --> vocal channel     --> MAIN AUDIO

Simplest genuine local-AI instrument:
 Keystation MIDI --> Logic MIDI instrument track --> MRT2 Small AUv3
                     [quiet fader + MUTE]          --> generated AUDIO
                                                            |
                                                   Logic main mix

Optional second control mode (already coded, NOT hardware-tested):
 Scarlett dry voice --> sounddevice --> voice_midi_bridge.py
                                          |
                                    CoreMIDI NOTE ON/OFF
                                          |
                            MRT2 standalone 'Magenta RT Input'
                                        OR configured IAC -> Logic MRT2 AUv3
```

The browser `stage_panel.py` currently captures Scarlett into its own Python sounddevice stream, asks Qwen for JSON notes and plays a low-level sine-based response through an independent PortAudio stream. **It does not control the Magenta AU.** Running the panel and voice bridge together can cause Scarlett device contention and should not be default.

PR #41's voice bridge is a deterministic **monophonic pitch-to-MIDI** converter, not a music AI listener. Current note gate waits two stable detections, releases after three silent detections and emits single pitch velocity 65. It has no chords, drums, MIDI clock, tempo grid, AI bar start or feedback from Logic.

## Newly identified testable gaps in PR #41

### 1. Latency geometry (theoretical, not measured)

`HOP=2048` at 48,000Hz = **42.67ms** per callback.
`WINDOW=2160` samples = **45ms** pitch observation.
The current loop accumulates samples until at least `WINDOW` then CLEARS that buffer, usually producing **one pitch observation per TWO 2048-frame callbacks**, or around **85.33ms**. The gate waits **two** stable observations for a pitch change. Roughly **170ms+** may pass before a new MIDI note is emitted; precise onset depends on buffer alignment and scheduling.

ADD actual CoreMIDI, engine control response (~200ms reported by Google in its system) and hardware/Logic output buffering: the full response is not proven to be tight enough for intentional swing or fast vocal syllables. **Never add the timings blindly to produce a guaranteed end-to-end latency number.** Measure actual microphone-to-generated-audio timing on the Mac, including cold/hot model state.

For expressive 90s rhythmic call-and-response, it may be better to detect an end-of-phrase at lower resolution then quantize AI permission at the **next bar boundary** in Logic instead of pretending the model can chase each syllable.

### 2. Pitch estimator failure modes

`estimated_pitch()` takes a 45ms PCM16 window, extracts one Scarlett channel and decimates by six without an anti-alias filter, then uses an autocorrelation estimator from `phrase.py`. Verify pitch stability with clean sustained voice, vibrato and VE-22 output. Filtering, window overlap, octave discrimination and note/voicing confidence should be measured before claiming voice following. High-noise processed vocals can create false notes.

Proposed QA recordings for **tests only**, using generated synthetic tones and original vocal input on the Mac: A3-C4-E4-G4 sustains, silence, breath/noise, deliberate pitch transition, vibrato ± semitone, clipped input, one-channel silent stereo input, and VE-22 doubling/harmony.

### 3. MIDI destination and silence safety

`MidiOut().get_ports()` must be checked against the **currently running** MRT2 standalone virtual port. The user's exact MIDI devices/index change when plugging in/out; no fixed IDs. An IAC virtual bus exists only if configured in macOS Audio MIDI Setup. In Logic, use one deliberate IAC-to-AU instrument track, verify no doubled trigger/feedback, and keep an independent mute.

`gate.panic()` sends Note Off, CC123 (All Notes Off) and CC120 (All Sound Off) when CTRL-C is handled. Abrupt power loss, device disconnect, app crash and blocked CoreMIDI aren't covered by that `finally` guarantee; an external MIDI kill/transport control must exist. Audit `Queue(maxsize=6)` overflow and stale-buffer behavior. Do not confuse stopping MIDI NOTES with instantly silencing previously generated MRT2 AUDIO: use AU track mute.

### 4. Missing musical context

The voice bridge carries PITCH not chords, beat placement, velocity nuance, rests as musical structure or Logic transport. MRT2 does not inherently hear the user's entire beat through the AU MIDI input. A full audio-reactive bandmate would require additional front-end beat/onset/harmony analysis and an appropriate engine conditioning API. The published model supports MIDI/style/audio prompt context; continuous live audio input remains a roadmap distinction. Keep our cultural research as DAW sound design guidance, not a claim the model has been trained on these records.

## The actual experimental ladder

| Stage | What the musician can play | What should count as success | What should NOT be claimed |
| --- | --- | --- | --- |
| **1: Magenta Jam Small** | Keystation directly to a music AI demo | Controlled real generated sound and easy mute | That it hears a microphone |
| **2: MRT2 AUv3 + Logic** | Keystation plays AI track on the same Logic session as user's beat | Separate low-level fader/mute, original beat never stops | That it's musically bar-synced or trained on Illmatic |
| **3: Voice MIDI → MRT2 Standalone** | Dry Scarlett voice controls MIDI input to official standalone | Correct monitored MIDI notes, no stuck notes, generated audio audible | That it hears the full vocal timbre |
| **4: IAC → MRT2 AUv3** | Voice pitch controller steers AI track within Logic | Independent control, reproducible route, immediate mute | That voice control is artifact-free or zero-latency |
| **5: Musical intelligence** | Approved human-made prompts, voice-gap sensing, chord and beat decisions | Suzy **prefers** new contribution over reference/baseline repeatedly | That adding albums to text prompts trained a jazz-rap model |

**Hard line for the Oct 29 show:** if any experimental AI path changes the stability of Logic beats, disable it and perform the rehearsed set. Never switch a known-good show to an untested model engine.

## Proposed scoped engineering PRs AFTER Mac verification

**PR A: AI engine boundary / routing config**:
- Keep current `stage_panel.py` Qwen controls as *Legacy Qwen audition* under a diagnostic path.
- Add stage-safe model selection **only for modes verified to work**: `MRT2 external MIDI` (no model download/run by SUZY//AI) or `Qwen demo`.
- Add service-owned MIDI routing to the actual discovered CoreMIDI endpoint with per-mode status, no duplicated Scarlett capture streams.
- Unit tests: absent port, wrong input channel, Note Off, silence, late response and STOP.

**PR B: Pitch pipeline / safety**:
- Improve DSP anti-aliasing and overlapped windows, confidence, timed debouncing and watchdog release without adding a heavy new ML library.
- Bench generated tones + actual Scarlett feedback; measure observed note-on latency and hanging note rate.
- Keep all audio callbacks free from inferencing/HTTP/blocking CoreMIDI.

**PR C: Performer MIDI actions**:
- Implement physical/keyboard actions `FOLLOW / GIVE SPACE / HOLD / UNMUTE / STOP` mapped to **control events**, not stylistic text that changes only after a late inference.
- All generated audio stays on a dedicated Logic track with a fader and independent mute; stop sends both MIDI panic and track mute where possible. Do NOT falsely advertise remotely controlled Logic mute without implementing it.
- Tests for extra MIDI route names, tempo changes and disconnect.

**PR D: Music context and human scoring**:
- Observe explicitly approved MIDI/chord and beat timing from Logic where APIs allow; use chord/Harmony to select notes entering the model.
- Track likes/dislikes of original AI generations as artist feedback, not training data without consent.
- Compare text-only Qwen vs music-native generation without genre/artist imitation.

## macOS check list before claiming integration

```bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.voice_midi_bridge --list-devices

# Mac system memory/swap and currently running processes:
sysctl hw.memsize
vm_stat
memory_pressure
# If AU not visible after installing host .app in /Applications:
pluginkit -mAv | grep -i mrt
```

Do not mix test or install instructions from other Python environments. In particular, using the **prebuilt Magenta app** does not require installing the heavy JAX/Python training environment into SUZY//AI. For a reversible first test, install official prebuilt Jam or MRT2 AUv3, **small model** only.

At review time the official sources do NOT establish: macOS 14.6.2 minimum compatibility for this downloaded build, actual MIDI input exposed in Jam vs standalone, memory pressure on the specific 8GB Mac under Logic, sample accurate bar sync in Logic, user model training/finetuning support shipped, or that our voice bridge has reached any physical interface. These remain actual hardware/software TEST ITEMS, not findings.

## Source links and legal context
- https://magenta.withgoogle.com/mrt2
- https://magenta.tensorflow.org/magenta-realtime-2
- https://github.com/magenta/magenta-realtime/blob/main/docs/apps/standalone_app.md
- https://github.com/magenta/magenta-realtime/blob/main/examples/mrt2/auv3/INSTALL.md
- https://github.com/magenta/magenta-realtime/blob/main/MODEL.md
- https://github.com/magenta/magenta-realtime/blob/main/docs/models.md

Source code and model weights have different licenses (Apache 2.0 vs CC BY 4.0). Google states it claims no output rights but users bear responsibility for outputs. Keep human-owned original music and avoid unlicensed samples, lyric cloning or deliberate artist imitation.
