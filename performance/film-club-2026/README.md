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

## First loop: immediate pedal handoff (updated)

On the **first** piano or other instrument take, press **DONE** as your phrase
ends. TOASTER closes the first MIDI phrase at the next *unscheduled eighth-note
tick*, rather than waiting to complete a full measure. Native Magenta
captures use the same shorter first-phrase period; the native Mac PCM engine
starts replay at the correct phase within about one small scheduling buffer
after the capture is processed, instead of waiting another whole loop.

The **drum metre, BPM, existing green beat-one cue and original start anchor**
remain intact. Like a hardware looper, a phrase that does not end on the
same bar division can create an intentional cross-rhythm against the backing
drums. If you want a strict four-bar pattern, press DONE near the matching
green one. Subsequent overdubs continue to follow the first loop's period.
This doesn't convert previously recorded browser or native PCM in memory.

The actual native loop still has unavoidable HTTP/capture processing latency
between DONE and playback; this fix eliminates the *extra full-cycle wait*
after that processing. Confirm with headphones on your Mac before using it
in the final film recording.

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

## v0.3: a livelier Pyramid, with an independent pedal per instrument

The Film Club view now defaults to **4/4 Propulsive electronica / breaks**
at the familiar **105 BPM**, without changing the Futureproof route's
default Soft Pulse. There's a **GROOVE ENERGY** slider and a second
**Frame-drum electro / syncopated** rhythm to try. Both are original
local synth patterns with moving kick/snare/hat and extra short percussive
subdivisions. The subdivision sounds are **browser synthesis**, not a
recording of traditional percussion or editable notes in the exported
three-lane GM MIDI. The meter/tempo and performance clock do not change.

The sound prompt directions apply to **all five native Magenta slots**:
piano gets repeating arpeggios and rhythmic chord attacks; cello supplies
a syncopated low counterline; violin adds expressive modal turns; glass/harp
gets rippling plucked ostinati; drums bring a driving breakbeat with
synthetic hand-drum-inspired accents. The original Pyramid chords
**F♯ → Gmaj7 → A6** remain. These are *conditioning prompts*, not
guarantees that MRT2 will output a particular drum beat. Audition each
sound and steer it with the keys before capturing.

**Violin/cello/glass/drums now share piano's immediate DONE behaviour.**
For any new native instrument take, wait for the familiar green beat one,
perform, and press **DONE → LOOP**. The first layer establishes the master
period. Later instrument layers can repeat at their own shorter
eighth-note-quantized durations instead of padding silence out to the
master's entire bar count. The piano foundation and other layers continue
unchanged; a short period that doesn't divide the master period may create
an intentional polyrhythm.

If you *don't* press DONE, the auto-finish still completes a full master
pass, as before. Keep in mind the Swift host requires a little
capture-stop processing before the replay becomes audible. It no longer
adds an avoidable full-period delay.

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
