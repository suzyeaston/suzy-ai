# SUZY//AI

**A human-led, local-first musical collaborator.** Play the instrument. Shape the AI. Keep control of the sound.

SUZY//AI is an open-source project by [Suzy Easton](https://www.suzyeaston.ca/) exploring live human–AI performance, musical interaction, original accompaniment, looping, memory, and cultural context. The current performance work is **The Appliance Latent Space** for Futureproof Festival in Vancouver on **October 29, 2026**.

The artistic direction is informed by 1990s hip-hop and R&B, Vancouver's own musical lineage, experimental electronics and live vocal layering. The goal is a responsive bandmate, **not** an imitation of another recording artist.

> The technology serves the music. The musician decides what enters the mix.

## Current state · October 25, 2026

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

## 🍞 SUZY//TOAST · research-grounded stage preview

**Draft PR #60; not a Logic plug-in yet.** The original *Appliance Latent Space* now has a little CSS toaster interface on the existing localhost MIDI stage at **[127.0.0.1:7345/toaster](http://127.0.0.1:7345/toaster)**. With the `magenta_stage` server running on macOS, its lever sends the already-supported Am7 MIDI test chord; LOW/DIRECT/HIGH, MIDI pause and MIDI release use the same safe bridge. Browning is a visual preview only. It never claims to control Google's AU neural parameters, Logic's track volume, or a durable recording.

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
