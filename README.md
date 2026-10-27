# SUZY//AI

**A human-led, local-first musical collaborator.** Play the instrument. Shape the AI. Keep control of the sound.

SUZY//AI is an open-source project by [Suzy Easton](https://www.suzyeaston.ca/) exploring live human–AI performance, musical interaction, original accompaniment, looping, memory, and cultural context. The current performance work is **The Appliance Latent Space** for Futureproof Festival in Vancouver on **October 29, 2026**.

The artistic direction is informed by 1990s hip-hop and R&B, Vancouver's own musical lineage, experimental electronics and live vocal layering. The goal is a responsive bandmate, **not** an imitation of another recording artist.

> The technology serves the music. The musician decides what enters the mix.

## 🍞 TOASTER PLAY · two-deck rehearsal instrument (October 27, 2026)

**Start here for a fast, human-led rehearsal.** On the 8 GB performance Mac, the new minimal TOASTER is a browser-local synthesizer, rhythm engine, chord-event looper, basic vocal looper and two-song mixer. No physical Keystation or running Magenta model is required to hear TOASTER's **own** instruments.

```bash
cd ~/Projects/suzy-ai
git switch main && git pull --ff-only
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
# Chrome: http://127.0.0.1:7345/toaster/live
```

Keep the Terminal open. The older complex mixer/timeline remains accessible at [`/toaster/studio`](http://127.0.0.1:7345/toaster/studio); **`/toaster/live` is now the simple PLAY view**.

### Live tempo, shared loops and chromatic notes

**The rhythm BPM control is now at the top beside Rhythm / Songs / Master**, instead of buried under settings. The rhythm and chord-event loops use one Web Audio transport epoch. A BPM change while playing is **applied at the next two-bar downbeat**, so chord loops, the playhead and pulses change together. New chromatic keyboard layout: **A W S E D F T G Y H U J K = C4 C♯4 D4 D♯4 E4 F4 F♯4 G4 G♯4 A4 A♯4 B4 C5**. Hold and release each key for note-on/off, independently of the four chord pads on **1 2 3 4**. MIDI notes go to the real native Magenta AU if it is on, and both live chords and melody are audible without Magenta.

Vocal capture now uses the **Web Audio clock and a fixed-length audio buffer**, instead of MediaRecorder's independent timer. The transport starts vocal takes on a session downbeat; playback uses the same beat epoch. Microphone capture timing can still depend on device/input latency, and is not a sample-accurate replacement for Logic, but no second unsynchronized loop timer is used. **After a recorded vocal/AI audio clip exists, tempo changes are safely blocked** rather than pitch-shifting the clip or silently desynchronizing it; export/delete audio clips before changing BPM. Chord/melody-event loops can freely follow BPM.

For actual Magenta, our native Audio Unit host also supplies **host musical context** (BPM, 4/4, continuous beat position) and sends note-on/off events when you play. This is **tempo guidance, not guaranteed beat-perfect generative synchronization**: Google's MRT2 AU currently reads the host beat position for transport-reset detection but does not expose a hard output-tempo-lock API. Keep AI drums filtered out and treat the neural layer as evolving accompaniment above the deterministic browser rhythm.

**On Swift build errors:** Swift 6.3.3 cannot compile against a macOS 27 SDK's Swift 6.4 interface. The updated `bash scripts/build-toaster-magenta.sh` selects an installed compiler/SDK pair that matches (including older macOS 26 SDKs and full Xcode), or exits with actionable instructions instead of showing pages of incompatible Swift-interface failures. If none are installed, install or select a matching full Xcode/Command Line Tools toolchain. Don't rerun the old command expecting an SDK mismatch to disappear on its own.

### Automatic Magenta launch and one-place sound controls (new)

**Starting the Python TOASTER server now automatically starts one real native Magenta AU host**, compiling the small local Swift helper if it has not yet been built. Browser synth/rhythm starts on PLAY RHYTHM because web browsers require a user interaction to start Web Audio. No Collider/Jam or separate ENABLE click is required for Magenta. The single native host stays alive across page refreshes; clicking STOP MAGENTA stops it until manually re-enabled or the server restarts.

The Magenta panel displays actual host status: compilation, AU detection, model path presence, native output sample rate, and whether **nonzero PCM was detected** at its native mixer. Nonzero samples alone don't prove a particular sound was synthesized correctly or played through the Scarlett. If the AU can't be found, its MRT2 Small model isn't installed, bookmark loading fails or output is silent, the ordinary browser instrument remains playable.

**Pyramid and Weird Fishes text prompts are now visible and editable** under EDIT THE TWO AI SOUND PROMPTS. Applying them restarts just the AI model to refresh Google's text embeddings, rather than pretending a live text edit is an instant timbre change. The SONGS crossfader continues to control the real Magenta prompt weights.

At the top are **ROOM FX**, **TONE** and **MASTER**. ROOM FX sends browser piano, pulse, recorded vocal and imported-loop audio through Web Audio convolution reverb and also sets the native Magenta hall reverb. TONE is a browser mix low-pass filter. Browser MASTER does not control the separate native AU output; use AI VOLUME / MUTE AI to control it. This is not yet a unified recording/mix bus for native-generated audio.

**If the model is still silent:** check the live AI status/diagnostics in TOASTER, keep the Scarlett as the macOS output and set audio devices to 48 kHz when required. View native errors with `tail -100 .build/toaster-magenta-stderr.log`. Do not run a second full MRT2 model in Collider, Jam or Logic at the same time on the performance Mac.

### First ten minutes

1. Keep **mic → BOSS VE-22 → Scarlett Solo USB**, as already wired. Connect headphones to the intended audio output. Click **PLAY RHYTHM**. TOASTER's own soft pulse starts and activates browser audio. With supported Chrome audio output switching, the app prefers the Scarlett; otherwise set **macOS Sound Output** to Scarlett. The output status shows when auto-routing is unavailable.
2. On **TRACK 01 / PYRAMID**, play chords with computer keys **1, 2, 3, 4**. **Press = note-on; hold = sustained chord; release = soft note-off.** The shortcuts keep working even after clicking PLAY RHYTHM, LOOP MY CHORDS or a song button. Chord pads also sustain while pressed and fade when released. Inputs and text fields are excluded so typing never plays accidental notes. No Keystation needed.
3. Click **LOOP MY CHORDS**. The app arms at the next two-bar boundary, records **chord note-on plus held duration** for the cycle, then repeats the chord with its actual held length and a natural release tail, rather than cutting off an audio capture at the loop boundary. Click again for another chord layer. Each loop has its own **MUTE** and **× remove**.
4. Click **🎙 LOOP VOICE**. Allow Chrome's microphone permission once. The app looks for a **Scarlett/Focusrite input** automatically (or uses the selected fallback). Sing via the **existing VE-22 → Scarlett** chain. Vocal capture is browser MediaRecorder audio with approximate boundary timing, not a sample-accurate DAW overdub.
5. Choose **TRACK 02 / WEIRD FISHES** and layer a second part. Use the **SONGS crossfader** to hear track 1, track 2 or a blend. Each deck retains its own clips and level controls.
6. Open **Sound settings / devices / export** only if needed to change the BPM, reverb, input/output, or **EXPORT WAV MIX**. The two-bar WAV is rendered offline from unmuted chord-event layers plus genuine recorded vocal / imported AI audio. Export before refreshing or closing Chrome: loops otherwise live only in browser memory.

### ✦ Real Magenta AU prompt engine (experimental, opt-in)

The simple TOASTER server automatically starts **one separate native macOS Audio Unit host** for the installed Google Magenta RealTime 2 Small model when you launch the Python app. An optional **STOP/ENABLE MAGENTA** button lets you silence or restart it without restarting the browser synth. This is a *real* native model audio source, not the browser's piano oscillator or a fake prompt. The two preset strings are installed as the AU's **MGRT_Prompts**, and the TOASTER song crossfader updates real AU parameters **Weight 0 / Weight 1**. Computer keys **1–4** send a direct **MIDI note-on** to that instance while held, and release sends a note-off. Looped chords also steer the same AU. The **AI VOLUME** slider now maps to Google's real Audio Unit dB gain (0% is silent; the default 28% is approximately -11 dB), **MUTE AI** flips Google's native mute, and **AI REVERB** adjusts a genuine native hall reverb effect after the model output. The browser's rhythm, song and master faders remain separate. **MUTE AI** silences only native Magenta: chords, existing recorded loops and your VE-22/Scarlett vocal routing keep working. Stop unloads the host. Google's **Filter Drums** and MIDI gate are activated so the model should not keep imposing busy beats between notes.

**Build once on your Apple Silicon Mac (requires a matching Swift compiler/SDK pair, a registered MRT2 AU, and local mrt2_small .mlxfn):**

```bash
cd ~/Projects/suzy-ai
bash scripts/build-toaster-magenta.sh
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
# Open http://127.0.0.1:7345/toaster/live and click ENABLE MAGENTA
```

The helper looks for MRT2 Small under `~/Library/Application Support/MagentaRT/models`, `~/Documents/Magenta` or `~/Downloads`. If needed, set `SUZY_MRT2_MODEL=/full/path/to/mrt2_small.mlxfn` **before** starting the Python server. No model downloads are performed. Do not run the separate Jam/Collider/Logic model simultaneously on the 8 GB Mac.

**Verification semantics:** `NATIVE AU RUNNING` means the native host and AVAudioEngine started; it **does not** independently prove that MLX loaded the requested weights or that musical audio reached Scarlett. `AI AUDIO SIGNAL DETECTED AT NATIVE MIXER` means the host measured nonzero audio samples on its real native mix bus, but headphones/system output still need checking. On first run, allow the model time to load and audition key 1 with the AI volume low; pause the browser pulse to distinguish the sounds. Native host output follows the macOS system audio device; browser and model volumes are independent. The new bridge's model bookmark/state restoration may need Mac-specific tweaks based on the locally installed MRT2 AU version. Test audio audibility before depending on the AI part of Thursday's performance.

**Loop capture limitation:** Native generated AI audio is not automatically sent into browser tracks or Loop Lab. For a genuine AI audio loop, print/bounce the model output via Logic or a supported audio-sharing route and import that audio file. The browser's native-generated piano/vocal loops remain entirely functional if Magenta fails to start.

### What is and isn't Magenta

**The TOASTER synth/rhythm/loop engine runs locally in the browser, not on Google Magenta.** With **ENABLE MAGENTA** and the optional native AU host built, the same two scene descriptions now become real AU prompt slots and crossfade weights. Without the native host, they are only labels and the browser's own piano remains audible. Pressing 1–4 can additionally send note-conditioning events to the existing `SUZY AI MIDI` bridge, but MIDI activity alone does **not** prove Google is generating sound, and the browser cannot mix, record or mute a separate Collider/Jam model automatically. Collider does not need to be open for this mode.

To loop **actual Magenta** audio today, print the output of **Google MRT2 Small inside Logic** and import the file using **+ IMPORT AI AUDIO**. The imported file then becomes a normal independently removable deck loop. The new native host provides an **alternative live Magenta path controlled from TOASTER**, so Logic is no longer necessary for *live AI generation* once that host is built and tested on the performance Mac. However, native Magenta audio is not yet routed into TOASTER's browser recorder. Logic remains the verified fallback for recording AI output. Do **not** run the native host alongside another full MRT2 instance in Jam, Collider or Logic on the 8 GB Mac.

**Known limitations:** Soft clock from Web Audio rather than Logic transport; browser mic capture is not guaranteed phase-accurate, output auto-selection requires `AudioContext.setSinkId` support and labelled device access; browser audio output does not control Google's separate host. Please test the complete mic/loop/print path on the physical Scarlett before relying on it for Thursday's show.

## Current state · October 27, 2026 (verified milestones and rehearsal caveats)

**The most important milestone:** On an 8 GB Apple Silicon Mac, **Google Magenta RealTime 2 Small** has been heard generating music as a **software instrument inside Logic Pro**, with a **Keystation Mini 32 MK3**, a **48 kHz Logic project**, **Scarlett Solo USB selected for Logic input and output**, and **headphones connected to the Scarlett**. The separate **MRT2 - Jam** app has also been heard responding to the Keystation.

**That neural instrument is Google's MRT2 Audio Unit, not a custom SUZY//AI Audio Unit.** This repository currently adds experimental MIDI steering, music-response research, and native looping tools around the creative workflow. The next engineering milestone is a **separately identified SUZY//AI AUv3 instrument/UI**, not an in-place modification of Google's working plug-in.

### Confirmed versus still being tested

| Area | Status | What that means |
| --- | --- | --- |
| MRT2 Small inside Logic | **Audibly confirmed on the performance Mac** | Google's MRT2 instrument generates music through Logic and the Scarlett headphones |
| Standalone MRT2 - Jam + Keystation | **Audibly confirmed** | The physical MIDI controller influences generated music |
| Logic audio routing | **Confirmed for this test** | Project at 48 kHz; Scarlett Solo selected as input and output; headphones audible |
| Mic → BOSS VE-22 → Scarlett | **Cables connected; complete vocal test pending** | The singer's Logic input monitoring, effects and actual vocal recording have not yet been independently verified |
| SUZY MIDI stage at `127.0.0.1:7345` | **Implemented; integration hardware QA pending** | Browser reports incoming Keystation events and creates virtual MIDI source `SUZY AI MIDI`; audible virtual-MIDI-to-Jam/Logic delivery has not been confirmed |
| Audio + Logic Setup UI | **Implemented as read-only discovery** | Lists CoreAudio inputs/outputs, including Scarlett candidates; **does not** switch Logic or MRT2 audio devices |
| Logic Live Loops / VE-22 looping | **Planned performance workflow** | Usable host/pedal features, but synchronized live set, overdubs and saved AI audio prints are not yet proven end-to-end |
| Custom SUZY//AI AUv3 | **Not built** | The proposed React-in-AU performance UI does not yet exist as a loadable SUZY instrument |
| Whole-set reliability | **Not yet certified** | Offline cold start, independent AI mute, audio print/save/reopen, and full 15-minute stress test remain |

**Do not interpret MIDI activity as proof of audible AI output.** MIDI, neural audio, vocal monitoring, and DAW recording are separate signal paths.

## The performance signal path

```text
Keystation Mini 32 MK3 ── MIDI ──► Logic software-instrument track
                                      │
                              Google MRT2 (AUv3)
                              mrt2_small neural audio
                                      │
                                      ▼
                              AI track / Logic mixer ──────┐
                                                          │
Dynamic microphone → BOSS VE-22 → Scarlett mic input ──► Logic vocal track
                                                          │
Prepared drums, synths, Live Loops ────────────────────────┤
                                                          ▼
                                                   Logic master output
                                                          │
                                             Scarlett Solo USB → headphones / PA
```

The **VE-22 is for vocal processing and optional foot-controlled vocal loops**. Magenta does **not** need to pass through the VE-22. Logic owns the main mix, the AI instrument fader/mute, the vocal track's monitoring, and recording.

An **optional** MIDI-steering experiment is:

```text
Keystation → SUZY//AI MIDI server → "SUZY AI MIDI" (virtual CoreMIDI)
                                            → manually selected MIDI input in Jam
```

This second path is **not** the confirmed Logic performance path. It does not output audio, read Logic's transport, control the MRT2 plug-in's volume, or guarantee an audio mute.

## Quick start: hear neural music in Logic

Use the already downloaded **official MRT2 bundle** and `mrt2_small`. See the [official Magenta repository](https://github.com/magenta/magenta-realtime) and our [Logic/MRT2 studio runbook](docs/studio-mrt2-logic-runbook.md).

1. Install **MRT2 (AU).app** in Applications and launch it once so macOS registers the Audio Unit. Keep the original Google plug-in as a known-good fallback.
2. Connect the Keystation and Scarlett Solo. Plug your headphones into the **Scarlett**, not the MacBook, if Scarlett is Logic's output.
3. In **Logic Pro → Settings → Audio → Devices**, select **Scarlett Solo USB** for input/output. In **File → Project Settings → Audio**, confirm **48,000 Hz**.
4. Create a **Software Instrument** track. Insert **AU Instruments → Google → MRT2 → Stereo**. Load `mrt2_small` if necessary. Start MRT2 generation, select/arm the instrument track and play the Keystation. Start with a low level.
5. Verify that Logic's AI track meter moves and audio comes from the Scarlett headphones. **Mute that track** to stop its audible contribution without silencing the rest of the Logic mix.
6. For vocals, use **mic → VE-22 → Scarlett microphone input** and create a separate **mono Audio** track in Logic. Select the correct physical input for your Scarlett generation. Set gains conservatively and monitor either through Logic **or** Scarlett Direct Monitor as appropriate, avoiding a doubled vocal signal.

For a dynamic microphone, don't enable phantom power unnecessarily. A processor's XLR output may be hotter than a bare microphone: lower the VE-22 output and Scarlett preamp gain if the input clips.

**Recording reminder:** A MIDI region steering a generative instrument is not necessarily an exact recording of the generated audio. Make and **listen to** a separate AI audio print or carefully verified Bounce in Place; save, close, reopen, and verify playback before relying on it during a set. Logic's own AI track mute is the immediate safety control.

**8 GB Mac tip:** For the live Logic test, quit the separate Jam and MRT2 standalone windows and leave Qwen stopped. Running multiple neural engines simultaneously consumes resources unnecessarily.

## 🍞 SUZY//TOAST · earlier MIDI-only stage preview (historical)

**Earlier implementation; not a Logic plug-in.** The original *Appliance Latent Space* now has a little CSS toaster interface on the existing localhost MIDI stage at **[127.0.0.1:7345/toaster](http://127.0.0.1:7345/toaster)**. With the `magenta_stage` server running on macOS, its lever sends the already-supported Am7 MIDI test chord; LOW/DIRECT/HIGH, MIDI pause and MIDI release use the same safe bridge. Browning is a visual preview only. It never claims to control Google's AU neural parameters, Logic's track volume, or a durable recording.

See [the toaster architecture, original control mappings and live Mac QA checklist](docs/suzy-toaster-roadmap.md). The October 26 research handoff explicitly recommends retaining the known-good Google's MRT2 Small AU inside Logic, keeping the human show path independent, and deferring a *separately identified custom SUZY AU* until after October 29.

## SUZY//AI MIDI stage · experimental

This repository's own browser interface steers **MIDI only**. It intentionally runs separately from the Qwen audition and does not start an audio engine.

On the Mac, after setting up the repository Python environment:

```bash
cd ~/Projects/suzy-ai
.venv-mac/bin/python -m pip install -e '.[live-midi]'
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
# Open http://127.0.0.1:7345/
```

Choose **Keystation Mini 32 MK3** under MIDI Setup in SUZY//AI. For a **standalone Jam** test, choose **SUZY AI MIDI** as Jam's MIDI input (instead of the physical Keystation), press Play in Jam, and audition the **TEST CHORD** or your own keys. If silent, switch Jam back to the physical Keystation to isolate a MIDI-routing issue from an audio-output issue.

| Browser action | Actual operation |
| --- | --- |
| DIRECT | Forward incoming MIDI notes unchanged |
| OCTAVE DOWN / UP | Transpose notes by 12 semitones |
| PAUSE / RESUME MIDI | Gate incoming notes; release held notes when pausing |
| TEST CHORD | Send a short Am7 MIDI-conditioning chord |
| RELEASE MIDI | Send note-off/all-notes-off messages; **not** neural-audio mute |
| Audio + Logic Setup | **Read-only** device discovery and host-routing instructions |

Seeing a Keystation event count only confirms that SUZY received notes. Even an active virtual MIDI port does not prove that Jam or Logic has selected it or that generated audio is audible. The MIDI bridge does **not** offer an output-device switch for Logic. Set output in the DAW or relevant standalone audio host.

Detailed instructions: [Magenta MIDI stage](docs/magenta-midi-stage.md) · [Studio routing and recording runbook](docs/studio-mrt2-logic-runbook.md).

## Live looping: practical separation of responsibilities

- **BOSS VE-22:** hands/feet-free vocal effects and phrase overdubs. Its vocal loop is not automatically aligned to Logic's bar grid and is not a permanent recorder; capture the output into Logic if you need to keep the take.
- **Logic Live Loops:** prepared drums, synths, quantized audio/MIDI clips, and live arrangement. Record vocals as audio cells or regions, and retain a separate audio print of any generative AI output you want to repeat exactly.
- **MRT2 Small (Google AU):** real-time AI musical generation conditioned by MIDI and its own model/prompt controls. The current custom SUZY browser does not directly control its audio or native parameter state.
- **SUZY native Mac looper (experimental):** a *separate* CoreAudio looper with capture, overdub, undo and optional DSP/model-guided variants. It does not become a Logic Live Loops track and does not replace the pedal. See [local looper](docs/local-looper.md).

The intended performance is **human vocals + prepared grooves + optional live AI response**, with the ability to remove the AI without interrupting the human music. Full musical synchronization and crash recovery are still QA tasks.

## Other research and tools in this repository

These are implemented experiments, not additional show-critical engines that must be running alongside Logic.

| Component | Purpose | Status and documentation |
| --- | --- | --- |
| Legacy Qwen performance panel | Scarlett mic phrase capture in memory, Qwen note-planning, basic synthesized audition | **Experimental, not a DAW plug-in or neural audio**. [Guide](docs/local-performance-control-panel.md) |
| Focusrite Python probe | Mic capture / DSP variation / vocal-sample rehearsal and approximate pitch analysis | **Experimental**. [Hardware QA](docs/live-hardware-qa.md) |
| Native SUZY Live Mac companion | Local CoreAudio looping, overdub/undo, optional response bridge and MIDI mappings | Separate app; host and latency QA remain. [Guide](docs/mac-companion.md) |
| Local Qwen3 AI core | On-device text inference, explicitly approved memory, musical teaching and cultural research | Separate service, **not** MRT2's neural audio engine. [Local chat](docs/local-chat.md) |
| Music culture packs | Research on 1990s hip-hop/R&B, jazz-rap and Vancouver/Rascalz history for original creative decisions | Inform optional text-based musical decisions; **do not** mean the audio model has learned these artists |
| Creative writing, reviews and threads | World model, album reviews, jokes and curated Top Ten material | Not part of the real-time audio signal path. [Top Ten workflow](docs/top-ten.md) |

### Optional older workflows

**Qwen phrase audition** (needs a separately running Qwen service):

```bash
bash scripts/start-mac.sh --api-port 7332 --model-port 8082
.venv-mac/bin/python -m pip install -e '.[live]'
.venv-mac/bin/python -m suzy_ai.music.stage_panel
# http://127.0.0.1:7344/
```

The older panel's **STOP AI** only stops its *own* Qwen audition. It does **not** mute the MRT2 instrument inside Logic.

**Native Mac looper, without a model:**

```bash
bash scripts/start-mac-companion.sh --looper-only
```

For the optional background DSP/model bridge, see [Mac companion setup](docs/mac-companion.md). The bridge normally uses port **7333**; Qwen core/model services use **7332/8082** in the example above. These are separate from the **7345** MIDI-stage server. Do not start every subsystem just to perform with MRT2.

For the Python AI core alone, `pip install -e .` installs the CLI; see [Mac setup](docs/mac-setup.md) and [local chat](docs/local-chat.md).

## What we're building next

**Near-term, for The Appliance Latent Space:**

1. [#46 · Confirm Logic MRT2 audio, separate recording, and reopening](https://github.com/suzyeaston/suzy-ai/issues/46)
2. [#47 · Verify an actual independent AI audio mute](https://github.com/suzyeaston/suzy-ai/issues/47)
3. [#48 · Offline / dropout / 15-minute show stress test](https://github.com/suzyeaston/suzy-ai/issues/48)
4. [#49 · Hands-free controls](https://github.com/suzyeaston/suzy-ai/issues/49)

**Custom instrument work:**

- [#59 · Build a distinct SUZY//AI MRT2 Audio Unit with embedded performer UI](https://github.com/suzyeaston/suzy-ai/issues/59). **Not yet implemented**; the installed AU is Google's.
- [#50 · Audible SPACE / ANSWER / TEXTURE behaviour](https://github.com/suzyeaston/suzy-ai/issues/50)
- [#51 · Performance vs Lab UX](https://github.com/suzyeaston/suzy-ai/issues/51)
- [#52 · Musical phrase timing and durable AI print](https://github.com/suzyeaston/suzy-ai/issues/52)

The architecture of Google's AU uses an embedded React interface and a native MLX music engine. We are researching a distinct, properly identified AU rather than changing the already-installed Google component. Official reference: [Magenta MRT2 AU](https://github.com/magenta/magenta-realtime/tree/main/examples/mrt2/auv3). Also relevant: [community AU template](https://github.com/audiohacking/magenta-au-template). Development/build/registration and real performance QA are still required.

## Related projects

| Project | Relationship |
| --- | --- |
| [The Appliance Latent Space](https://github.com/suzyeaston/appliance-latent-space-live) | Earlier experimental browser sequencing and visuals |
| [POP//CONTEXT](https://github.com/suzyeaston/pop-context) | Audiovisual/media-context research |
| [SUZY//WORLD](https://github.com/suzyeaston/suzy-world) | Published reviews and structured cultural material |
| [suzyeaston.ca](https://www.suzyeaston.ca/) | Public creative lab |

These projects share a creative direction but **are not all integrated into a single live performer system**. The [app registry](config/apps.json) and `scripts/sync-apps.sh` track related checkouts.

## Development, testing and data

Python core and backend tests:

```bash
bash scripts/test.sh
python -m unittest -v tests.test_magenta_midi tests.test_magenta_stage tests.test_audio_routing
```

Native Mac companion tests (macOS with build tools):

```bash
(cd apps/macos && swift test)
bash scripts/build-mac-companion.sh
```

Hardware-free tests verify contracts, not the sound, DAW audio routing, or MIDI hardware on a real Mac. Read [studio preflight](docs/studio-mrt2-logic-runbook.md) before declaring the performance ready.

Private, explicitly approved world/memory state lives under `~/.suzy-ai/` by default and is **not** populated when someone clones this public repository. Mac looper audio is in memory until explicitly saved. Magenta model assets are managed separately from this repository.

Further reading: [architecture](docs/architecture.md) · [world-model storage](docs/world-model.md) · [teaching surfaces](docs/teaching-surfaces.md) · [build notes](docs/build-in-public/).

**License:** [Apache-2.0](LICENSE). External Magenta model assets, native plug-ins and source have their own documentation and applicable terms.
