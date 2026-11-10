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

## v0.6: long jazz chords + sustained native note audition

This version corrects two practical problems with the Film Club sound:
**HEAR** used to only change a five-prompt weight, not actually play an
instrument; and the native Swift host defaulted to a **480 ms minimum
chord hold**. Short taps therefore sent MIDI note-offs before Google's
neural audio could develop the sustained texture you wanted.

The five **HEAR** buttons now set the matching *real* Google MRT2 prompt,
apply the current **NATIVE CHORD SUSTAIN** (2.4 s by default), send a
single actual F♯-centred harmony chord and release it through the existing
native engine. The host holds it for the full configured minimum even if
you release the browser control instantly. Holding Z/X/C longer still
works, and a new chord cancels a pending old note-off rather than being
cut off by it. Use the slider from 0.4 to 4.8 seconds to audition
slow-moving voicings. Changing it does **not** restart MRT2, replace
your five prompt texts, alter the loop period, or overwrite PCM takes.

The **original Futureproof default remains 480 ms**. This longer value
is applied only after a Film Club performer deliberately touches HEAR
or changes the new sustain slider. Be aware the two pages share one
live native host, so the last deliberately applied sustain setting
remains on that host until it is restarted or changed again.

The revised Film Club prompt palette is one part **swung suspended jazz**
and one part **spectral futuristic electronics**. It emphasizes deep
voiced piano chords, long bowed cello and violin lines, ringing
vibraphone/glass harmonics, granular decay, brushed backbeats and
low electronic pressure. The clock still runs at 100 BPM 4/4 but
the pitches/attacks float around it. These are original direction
prompts, not a transcription of anyone else's composition.

### First listening test

1. Start the rhythm and load `mrt2_small` in Google's Audio Unit.
2. Apply the revised Film Club prompt bank if the Google popup still
   shows the previous version. Export valuable takes before a prompt
   restart.
3. Click **HEAR PIANO** once; it now actually triggers an audition
   chord. Listen for a long resonance, not a 480 ms blip.
4. Click **HEAR CELLO**, then **HEAR VIOLIN**. Each sends the same
   chord under a different weight, so the timbre can be compared.
   Use the status message and native model popup to check the
   instrument weights; this does not promise the model *sounds*
   correct without listening.
5. Try holding a real Z/X/C key for four seconds, then releasing.
   Use **RECORD TAKE → DONE → LOOP** for separate genuine PCM layers.
6. Once you like the individual instruments, try **BLEND ALL FIVE**
   to hear a sustained composite generated sound. Five separate
   looping tracks still require five separately recorded takes.

Changing the sustain only affects *future MIDI notes*, not already
recorded native audio.

## v0.5: actually audition the five native sounds + perform the accelerando

**Why only piano?** Google's official MRT2 is one AU generating **one
blended audio stream** from five text prompts. In the native Swift mixer the
usual startup weights are **piano 100%, all other prompt slots 0%**
(`configure()`, AUParameter addresses 10 through 14). Loading five
different prompt strings does **not** make five separate instrument
channels appear. A slider weight of zero makes that prompt inaudible.

The Film Club screen now displays a visible **Hear a voice** board:
**HEAR PIANO / CELLO / VIOLIN / GLASS / DRUMS** and
**BLEND ALL FIVE · ONE GENERATOR**. These call the original tested
`selectNativeLane()` routing function, not a duplicate music engine;
the board reads back the Audio Unit's real five `prompt_weights`
and reports the selected weight. Click **HEAR CELLO** to send a real sustained audition chord, then
hold Z/X/C for an even longer performance if you want. The piano and
other prompts are selected in turn for comparison.

**BLEND ALL FIVE** intentionally sets five nonzero native weights
(roughly 31/20/19/16/15%). This creates *one combined model texture*.
To actually have five **independent looping instruments**, keep using
the separate existing **RECORD AI [INSTRUMENT] TAKE → DONE → LOOP**
pedals. Capture one role, then audition/capture the next. Previously
recorded native-memory PCM remains a separate loop until deleted or the
native generator is restarted. These audition buttons never change
the five prompt texts or restart MRT2, and they refuse to switch while
a take is being captured. Press PLAY RHYTHM and audition keys as
usual: the selector itself does not generate notes.

### What ACCELERANDO contributed to this original arrangement

Research on the October 2026 Grimes/VADAKIN track identifies a
large bass-driven electronic rhythm, timbral abrasion, contrasting
slower middle section, and subsequent renewed drive. Rather than
copying its specific sounds, lyrics, melody, or vocal arrangement,
this Film Club score borrows **the dramatic shape**. Radiohead's
*Pyramid Song* is actually grounded in 4/4 but its piano chords
float/swing across the pulse. Philip Selway described responding to
the inflection of the piano rather than counting mechanically.
We retain the F♯ / Gmaj7 / A6 suspended colour and human looseness,
then gradually layer original electronic movement around it.

Sources for musicians to explore:
- https://pitchfork.com/reviews/tracks/grimes-vadakin-accelerando/
- https://www.spinmagazine.com/2023/01/radiohead-philip-selway-interview/
- https://mtosmt.org/issues/mto.13.19.1/mto.13.19.1.hesselink.html

The five Film Club **time cards are now live density gestures**. They
change only the browser percussion energy and its per-beat subdivision
count (plus local rhythm level), **never 100 BPM, song meter, native
MRT2 settings, or saved PCM loop period**:

| Card | Local gesture | Listen for |
| --- | --- | --- |
| 0–10 | Low-energy beat, no ghost subdivisions | Weighted piano resonance and Gastown |
| 10–24 | More percussion subdivision | Cello counter-pulse and sparkling glass |
| 24–38 | Dense subdivided strokes, stronger level | Machine pressure and distortion in layers |
| 38–48 | Near-silent rhythm, half-time *feel* | Violin/voice as human interruption |
| 48–60 | Partial return | More open, unresolved harmonic end |

The cues are artist-operated, not automatically synchronized to Gastown
Simulator or the music transport. Start with solo piano and bass, record
them as independent takes, build through layers, and only then use the
BLEND option if you want to audition a composite native texture.
The sound prompts are per-instrument and avoid demanding a whole
dance arrangement from every slot.

## v0.3: a livelier Pyramid, with an independent pedal per instrument

The Film Club view now defaults to **4/4, 100 BPM Electro house ·
four-on-the-floor**. It has actual local quarter-note kicks on beats 1,
2, 3, 4; snare/clap accents on 2 and 4; offbeat hats; plus a
**GROOVE ENERGY** slider (24% at startup; raise it with the live cues). The alternative
**Frame-drum electro / syncopated** and **Propulsive electronica / breaks**
rhythms remain available. These are original browser-synth sounds, not
samples from artists or editable notes for the extra ghost subdivisions
in the GM MIDI export. This Film-only preset does **not** change the
Futureproof route's 105 BPM Soft Pulse. Before any first recording,
the Film Club script sets the actual transport to 100 BPM. Never
change the tempo under an existing PCM loop; the live engine blocks it.

The sound prompt directions apply to **all five native Magenta slots**:
piano gets weighted irregular suspended chord attacks, cello plays
a woody pizzicato pulse with occasional bowed slides, violin stays
expressive with urgent tremolo and long releases, glass is resonant
and granular, and the 100 BPM drum prompt becomes a dark, shifting
break/house hybrid rather than five generic repetitive house parts. The original Pyramid chords
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

## Important: the native Google UI can retain the ORIGINAL prompt bank

A prior version of this app incorrectly treated the **Swift host's own
`text_prompts`** as proof that the five Film Club prompts were active
inside Google's Audio Unit. That claim was wrong. This code now reads
`MGRT_Prompts` from the instantiated **Google AU's own `fullState`**
and shows it separately from the host's requested strings.

Even a matching AU `fullState` does **not** prove the model is using
the new text embeddings, or that Google's window reflects them. In
Google's upstream AUv3 source, bookmark autoload and the built-in model
selector take different paths. The selector's `loadModelAtPath` does
not reapply `set_text_prompts` after loading a model from the UI.
See `examples/mrt2/auv3/MagentaRT_AudioUnit.mm` in
`magenta/magenta-realtime`. We cannot safely patch Google's installed
extension or claim to have remotely edited its proprietary runtime.

### Reliable path with the official Google window

1. Export any important native in-memory audio loops first.
2. Open Film Club and, if necessary, use **APPLY FILM CLUB SOUNDS TO MRT2**
   to request the saved bank, confirming the native restart.
3. Look at the new status: a host match is not a Google AU match.
   If the Swift binary is old, run `bash scripts/build-toaster-magenta.sh`
   from the repo checkout and relaunch the stage.
4. Open the native Google model window. If its five prompt rows still display
   old strings, use **COPY 01 / 02 / 03 / 04 / 05** in the new
   **When Google's window still shows the old sounds** panel.
   For each matching Google prompt row, select the old text and paste
   the copied Film Club text (Cmd+V), confirming the edit inside Google.
5. Listen after each prompt switch. This uses Google's own supported UI
   event path, which calls its running engine's `set_text_prompts`.
   The Google popup is the source of truth for prompt edits; the
   in-app status cannot attest to auditory correctness.

Copying text never restarts or changes anything automatically, so you can
work through these rows deliberately and avoid needlessly wiping loops.

## Why the Google MRT2 popup still showed the original prompts

The Film Club HTML rendered five new text boxes, but Google's separate
**native AU popup** still showed the original Futureproof sound bank.
Changing the page or refreshing Chrome does **not** automatically reconfigure
a running Audio Unit. The stage starts its native model with the normal
default bank, and we intentionally do not overwrite it just by navigating.

The Film Club view now has a prominent **APPLY FILM CLUB SOUNDS TO MRT2**
button next to the prompt editor. Above that button the app reads
`/api/ai/status` (without modifying the model) and compares all **five
actual native-host `text_prompts` values** with the five visible Film Club
textarea values. It shows an explicit mismatch instead of merely claiming
the page has loaded a new sound.

When you click APPLY:
1. Export native in-memory audio takes you want to keep, then confirm the
   restart. The app reports the active native loop count if available.
2. The existing TOASTER action stops the shared native generator, configures
   five Film Club text prompts, then starts the **same** Audio Unit.
3. The Film Club panel reads back the host's text bank and reports either
   **host verified**, **still starting**, or **NOT VERIFIED**. It never
   claims the new sound is proven audible merely from a status response.
4. If the Google AU popup is still showing a stale page after the host
   reports the new text, **close and reopen that native window** and
   select the local `mrt2_small` model again if it asks. This interface
   belongs to Google, not the browser.

The underlying `/toaster/live` source continues to display the
Futureproof text presets. Both pages control the **same running Audio
Unit**, so the actual active prompt bank can be either version depending
on which one was most recently applied. To switch back, visit
`/toaster/live` and apply its prompts deliberately. Never rely on a
browser refresh to restore the native host.

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
