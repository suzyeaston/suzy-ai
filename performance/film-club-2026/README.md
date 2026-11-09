# PYRAMID / SOFT RESET · BC + AI Film Club

**Same hands-on SUZY//TOAST instrument, new composition-specific sound prompts.**
A musical continuation of Suzy Easton's October 29 Futureproof Pyramid Orbit
performance for the Film Club's *Make Art Not War* music video, with Gastown
Simulator as the visual world.

The creative direction is **a continuation of the Pyramid theme**, not a
new automatically composed one-minute song. The F♯ → Gmaj7 → A6 harmonic
space is the anchor. Build the film's tension with layered takes and a musical
accelerando, then resolve with the performer, voice and violin. Grimes'
accelerando is a conceptual reference to acceleration and density, **not**
a request to imitate recordings or reproduce another composition.

## Open the actual looping instrument

This is the important URL after updating your local checkout:

**http://127.0.0.1:7345/film-club/soft-reset/**

The more descriptive alias **http://127.0.0.1:7345/film-club/pyramid/**
does exactly the same thing. The Film Club page is rendered from the
**unchanged existing** `suzy_ai/music/toaster_play.html` performance
instrument. It is not a second loop engine or a static synth sequencer.

```bash
cd ~/Projects/suzy-ai
git switch main
git pull --ff-only origin main
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
```

If that Python environment does not exist, use the Mac setup described in
`docs/mac-setup.md`. A locally installed `python3` environment with the
required MIDI bindings may also run `python3 -m suzy_ai.music.magenta_stage`.
Open Chrome after the local stage announces port 7345. Do **not** launch a
second copy of MRT2; the existing stage owns one native AU host.

The earlier `http://127.0.0.1:8787/performance/film-club-2026/` is still
available as an **archived 60-second synthetic score sketch**, with an
explicit link at the top to the new performance view. It is no longer the
primary Film Club instrument.

## What is reused unchanged from Futureproof

- Floating 1–4 beat clock; record on the highlighted green beat 1.
- One **RECORD FIRST LOOP → DONE → automatically repeating PLAY** workflow.
- Add real audio layers, adjust/mute/solo/hold/silence clips, and keep the
  original first-track bar alignment.
- Piano, violin, cello/harmonium, glass/harp, native drums and voice lanes
  with their genuine separate PCM record/loop pedals.
- Scarlett / VE-22 microphone inputs; browser key pads; browser synth
  fallback; Magenta RealTime 2 optional native AU; per-lane levels and FX.
- `SAVE PYRAMID WAV`, full-set audio recording, safety controls and
  unchanged keyboard shortcuts.
- Existing on-screen Pyramid harmony, not a prepared recording of Radiohead.

No previously recorded browser loop is bundled into GitHub. These loops
live in the **running browser memory**, and native AU memory loops live in
the process. Before changing versions or prompting a native restart,
**export what you care about**. Opening the new route does not migrate
an in-memory take from another tab.

## Five Film Club prompts

| Original native slot | New instrument direction |
| --- | --- |
| 01 · Pyramid piano | Close felt piano, suspended harmony and human rubato |
| 02 · Cello/harmonium | Bowed cello, warm sub shadow, slowly changing texture |
| 03 · Violin | Fragile expressive strings, tremolo into lyrical legato |
| 04 · Glass/harp | Rain-reflection glass, celesta and irregular metallic decays |
| 05 · Drums | Brush and tom pulse into syncopated accelerating movement |

These are **alternative text inputs on the Film Club page only**.
`/toaster/live` continues to display the original five Futureproof
prompts. The original Python prompt constants and audio host code remain
untouched.

**Important limitation:** both pages control the **same** native
Magenta Audio Unit when connected to the same stage. Editing Film Club
prompts in the browser does nothing to the model until you deliberately
press **APPLY PROMPTS** (or start a stopped host from the film page).
That restart can silence/clear unsaved **native memory loops**. The Film
Club page asks for confirmation before APPLY. It cannot promise concurrent
independent model configurations. To return to the Futureproof sound, open
`/toaster/live` and reapply its original prompts, once your takes are safe.

## Gastown film edit guide (not a second clock)

| Proposed cut | Performance arc | Visual idea |
| --- | --- | --- |
| 00–10s | Piano, held breath | Gastown as it is |
| 10–24s | Glass and cello enter | Reflections repeat |
| 24–38s | Rhythmic density and tremolo | Technology accelerates |
| 38–48s | Drop to voice and violin | The human interrupts |
| 48–60s | Harmonic return | Make art not war |

The Film Club page has a **SAVE GASTOWN 60s CUES JSON** control. The file
supplies suggested editorial cue times to align with screen captures. The
loop engine's native transport remains freely performed; this **does not**
claim sample-accurate automatic syncing of the game and music. Record/export
your audio first, then line up the film edit to the soundtrack.

## Verification

```bash
python3 -m unittest tests.test_film_club_pyramid tests.test_soft_reset_stage
node --test tests/toaster_play.test.cjs
```

Tests check that the film view contains the complete original controls
and scripts, that the source page is unmodified, that exactly five
view-specific prompts replace the text fields, and that local query
parameters and song assets route correctly. Existing original TOASTER
unit tests continue to protect capture, playback and safety logic.
A Mac headphones/audio-device rehearsal remains necessary to verify the
real Magenta AU and microphone takes.

The earlier `score.js`, `audio.js`, `app.js` and WAV-render tests remain
in the repo as an archive of the standalone sketch, not the live Film Club
composition.
