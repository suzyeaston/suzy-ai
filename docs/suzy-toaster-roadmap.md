# SUZY//TOAST: Appliance Latent Space inside Logic

**Status (2026-10-26):** Browser-based, localhost MIDI-control **prototype**. Not yet a Logic-hosted Audio Unit. This scope is deliberately small because the known-good **Google Magenta RealTime 2 Small AUv3 inside Logic Pro** is already audibly confirmed on Suzy's 8 GB Apple Silicon Mac.

## Decisions from the October 26 research handoff

This PR follows the *Rehearsal and Future-Proofing Research: SUZY//AI, Magenta RealTime, and The Appliance Latent Space* handoff rather than treating the toaster as a cosmetic rebrand.

1. **Do not replace Google's working AU before Futureproof (October 29).** Direct Keystation → Google's MRT2 Small AU on its own Logic instrument channel remains the fallback.
2. **One owner per signal path.** Logic owns audio, recording, track mute, prepared loops and monitoring. The VE-22 → Scarlett vocal chain is independent. The optional localhost bridge only forwards MIDI to a virtual `SUZY AI MIDI` port.
3. **SPACE must mean audio silence.** A web button that sends MIDI Note Off cannot stop a streaming neural generator. Only Logic's actual AI-track mute is authoritative *now*; no pretend `STOP AI` on the toaster.
4. **ANSWER is an entry policy.** The first lever demonstration uses the existing `/api/test` Am7 note cue. It does not imply that MRT2 hears or understands microphone audio.
5. **TEXTURE means real style/model conditioning *later*.** Google exposes MIDI and prompt/embedding controls, but the current SUZY bridge has no live access to AU parameters. Current page offers octave transforms, not a fictitious style knob.
6. **Keep the original shared control vocabulary.** The canonical source is `suzyeastonca/assets/data/appliance-latent-space/control-map.json`, mirrored in `appliance-latent-space-live/src/core/control-map/control-map.json`; do not move its CCs or overwrite the semantic meaning.
7. **Protect the 8 GB Mac.** This page has no framework, font download, image assets, model dependency or local inference. Qwen and Jam need not run for the known-good Logic direct path.

## What this first PR implements

- A tiny cheerful CSS toaster with toast/lever animation and large stage actions at `http://127.0.0.1:7345/toaster`.
- Uses **the same localhost, token-protected MIDI endpoints** as the existing Magenta MIDI stage, with *no new device routing*.
- Lever / **TOAST A CHORD**: existing short Am7 MIDI cue (`/api/test`), explicitly **not a Magenta audio-confirmation indicator**.
- LOW / DIRECT / HIGH: existing −12 / 0 / +12 semitone `/api/mode` transformations.
- PAUSE / RESUME MIDI: existing `/api/gate`, releasing held MIDI notes on pause.
- EJECT / RELEASE MIDI: existing `/api/release`, explicitly **not an audio kill**.
- Browning slider: a **visual-only** working prototype corresponding to future CC 21, with no MIDI, tone, or Logic claim.
- Keyboard selection and local-bridge status, intentionally labelled `AUDIO UNVERIFIED`.
- Escape MIDI release, Shift+1/2/3 for octaves, Shift+G for MIDI gate, and reduced-motion styling. Unmodified global Space/Enter to avoid hijacking Logic/browser shortcuts.
- Existing localhost origin/token/JSON safety policy and no external dependencies.

### Audio I/O and loop setup now present on the page

The toaster exposes two prominent navigation anchors: **Audio I/O** and **Looping**.

- **Audio I/O** calls the existing read-only `GET /api/audio-routing` route and shows input and output capabilities, Scarlett candidates and macOS defaults separately. No stream starts and no setting changes. Even a listed Scarlett or system default is **not verification** that Logic selected it. In Logic's **Settings → Audio → Devices**, set Scarlett input and output; in **Project Settings → Audio**, confirm **48 kHz**.
- **Looping** provides a **rehearsal duration reference** (BPM, beats/bar, bars) and practical instructions for three actual loop owners: **Logic Live Loops** for synchronized/quantized musical clips, **BOSS VE-22** for independent vocal pedal capture, or the experimental **SUZY Live native looper**. This is intentionally **not a recorder or a DAW sync/control layer**.
- The actual capture/overdub/undo controls belong to Logic, the pedal, or the separate native app. The native looper supports one loop with overdub and undo and requires separate Mac/audio QA. Its clock-sync mode is experimental. See `docs/local-looper.md`.

We should **not** implement pretend input/output dropdowns that never change the host, nor simulated recording controls labelled CAPTURE that do not capture sound. Actual routing and looping controls for the future custom Audio Unit require a host integration design, tested state and explicit recording/monitoring contracts.

### Canonical control mappings (reserved, not secretly implemented)

| Control ID | MIDI | Meaning / proposed custom AU implementation |
| --- | --- | --- |
| `browning` | CC 21 | Warmth/tone **post** neural generator |
| `destruction` | CC 22 | Saturation/glitch **post** generator |
| `latent_x`, `latent_y` | CC 23, 24 | Real prompt/PCA surface navigation in a custom `magentart::core` host |
| `neural_mix` | CC 25 | Independently controllable **AI audio** gain / blend |
| `memory` | CC 26 | Prefill/state or short-term effect memory, as auditioned |
| `freeze` | note 38 | Hold chosen state or scene |
| `plunge` | note 36 | New gesture / intentional transition; the current lever is only a *test-chord stand-in* |
| `capture` | note 37 | Save audio/state/scene only after durable recording is implemented |
| `kill` | note 39 | Real mute of neural **audio**, not only All Notes Off |

Source: historical Appliance control map, consistent with October 26 research handoff. All six continuous control values normalize to 0–1; do not arbitrarily assign their ranges to undocumented AU parameters.

## Try the toaster safely

On the performance Mac after confirming direct Keystation → Google's MRT2 AU still works:

```bash
cd ~/Projects/suzy-ai
git fetch origin
git switch feat/suzy-toaster-stage-preview
.venv-mac/bin/python -m pip install -e '.[live-midi]'
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
# open http://127.0.0.1:7345/toaster
```

**For the bridge experiment, use MRT2 Jam first, not the Thursday show project.** Connect the physical Keystation in toaster Setup; select only `SUZY AI MIDI` as the MIDI input inside Jam; play the test cue with Jam's output level low. The bridge is not a Logic plugin and the webpage cannot select a MIDI port in Google's AU. To recover, close the experimental bridge and select the physical Keystation in Jam/Logic.

**Hardware listening checklist (must be completed on actual Mac):**

- [ ] CSS toaster renders; keyboard-selected / unknown states accurate; browning only affects illustration.
- [ ] Existing MIDI stage at `/` still works; same 7345 server.
- [ ] Jam chooses `SUZY AI MIDI` **instead of** the physical Keystation; no doubled notes.
- [ ] Toast lever sends Am7 cue, actually audible as a *Magenta* reaction (not merely a note-event count).
- [ ] LOW / DIRECT / HIGH change audible MIDI conditioning; note release remains clean.
- [ ] EJECT releases notes but does **not** claim to mute continuous audio.
- [ ] Experiment failure / browser close doesn't stop prepared Logic backing or vocal chain.
- [ ] Direct physical Keystation → official Logic MRT2 AU still works after switching back.

These *software* checks run without Mac hardware:

```bash
python -m unittest -v tests.test_magenta_midi tests.test_magenta_stage tests.test_audio_routing
```

This test suite **cannot** certify neural audibility, a 48 kHz Scarlett session, audio print/reopen, offline cold start, or a 15-minute dropout-free set. Those are separate hardware/Logic rehearsals. **Do not merge this PR into the Thursday performance workflow merely because CI is green.**

## Follow-on PRs: what becomes a true Logic instrument

1. **After Futureproof: AU host spike.** Build a *separate* `SUZY//TOAST` Audio Unit with independent bundle identity (not overwritten Google AU), using Google's `magentart::core` / official examples as the inference host. Check current APIs and license/attribution at implementation time. Retain Google's AU as rollback.
2. **Make its interface an instrument, not a settings page.** Toaster face and large lever on stage; dedicated setup/diagnostics screen. SPACE / ANSWER / TEXTURE as intentional, tested performer actions.
3. **Connect real parameters.** Wire dedicated gain/mute at the native audio output, post-AI tone/saturation, approved note gating/scale/chord shaping, and auditioned PCA/prompt-blend controls. Avoid treating a style embedding as live mic listening.
4. **Prove Logic integration.** Audio Unit validation + tested Logic host at 48 kHz, automation save/restore, independent AI audio print and mute, predictable memory/CPU and fallback within ~10 seconds.
5. **Artist-owned sonic identity.** Collect provenance-clean original voice/bass/appliance samples outside source control, build embeddings/prompts, and defer actual MRT2 fine-tuning until an upstream supported training path exists.

Do not claim tests have run on the performer Mac until they actually have. The core musical decision stays Suzy's: **human music first, neural sound optional, actual mute under the musician's control**.
