# PYRAMID / SOFT RESET · BC + AI Film Club

**Same hands-on SUZY//TOAST instrument, new composition-specific sound prompts.**
A musical continuation of Suzy Easton's October 29 Futureproof Pyramid Orbit
performance for the Film Club's *Make Art Not War* music video, with Gastown
Simulator as the visual world.

The Film Club composition now uses a **four-chord Accelerando-derived
rehearsal adaptation** rather than the old Pyramid F♯ progression:
**Em → E7 → Am → E**. This selection follows the four prominent chords
listed by Mazmazika (it is not the complete song transcript). Hooktheory
analyses sections in E Phrygian Dominant and a bridge in E minor, at
124 BPM in 4/4. The film deliberately retains our 100 BPM, 4/4 loop
clock, the original TOASTER recording workflow, and the warmth of the
Pyramid piano, cello, harmonium and violin.

**E7 matters:** E minor's G-natural becomes G-sharp in the dominant
seventh (E–G♯–B–D), then resolves through A minor before opening into E
major. F-natural can appear as a sparse Phrygian-dominant colour, not an
invented fifth chord. The original Futureproof F♯/Gmaj7/A6 song remains
unchanged at `/toaster/live`.

Sources:
- https://www.mazmazika.com/chordanalyzer/grimes-vadakin-songs/accelerando-chords
- https://www.hooktheory.com/theorytab/view/grimes/accelerando-ft-vadakin

## NEON SYNTH v1.1: playable electronic instruments, no Google prompt paste

The Film Club route now opens with its **Pyramid/Accelerando keys set to
LOCAL NEON SYNTH**, not the older Google AU sound bank. Z/X/C/V chord
pads play a real Web Audio synth piano: detuned saw and triangle partials,
a transient FM modulator that stops at each note release, a descending
brightness response and four short sixteenth-note arpeggio pickups.
**This instrument works without Google MRT2 being loaded**; it is not
misrepresented as native AI audio. The original 100 BPM shared looper,
stored takes and Futureproof source remain unchanged.

The Film-only local instrument presets now include NEON FM SYNTH PIANO,
GLACIAL SUPERSAW PAD, PIXEL GLASS PLUCK, RUBBER ANALOG SUB, NEON SAW
LEAD and SHARP DIGITAL ARP. Switch instruments with the original local
instrument picker and record loops normally. The main Film control bar
has an explicit **NEON SYNTH PIANO · ON** button: click it to toggle
back to the optional native Google piano lane. If you select native,
Google's sound may still reflect an older bank; that is a separate AUv3
limitation, not a reason to stop local music.

Five new *optional* native Magenta sound prompt ideas are provided for
future Google audition: bright FM keys, sidechained analog sub, supersaw
lead, granular digital glass and fast electronic club drums. They
replace the old acoustic-first Film Club prompts in the text editor.
Because Google's installed AUv3 does not reliably re-embed host-written
`MGRT_Prompts` after loading the model through its GUI, a browser-side
"Apply" cannot guarantee these native sound prompts will take effect.
The Google prompt panel is now collapsed under **OPTIONAL · GOOGLE MRT2
SOUND BANK (ADVANCED)**, rather than presented as the gatekeeper to making
music. This release does **not** claim the native Google plugin has been
patched or that its sounds automatically changed.

**Recording:** Local synth audio is the browser instrument bus and is
captured by the existing live loop/recording workflow. Google's separate
native stream still requires system audio capture (OBS or screen+system
audio) to get both into Logic Pro. If no sound is heard, first select
NEON SYNTH PIANO · ON and play Z/X/C/V after unlocking Chrome audio.

## v1.0: more buoyant Accelerando-inspired instruments

The harmony stays **Em → E7 → Am → E** and the one shared looper
clock stays **100 BPM / 4/4**. The Film Club bank now gives every
instrument an active rhythmic role rather than asking the entire ensemble
to float on long sustained notes:

- **Acoustic piano:** bouncing eighth-note figures, clipped offbeat chords,
  quick sixteenth-note pickups and octave answers; suspended resonance remains
  underneath instead of swallowing the attack.
- **Cello + harmonium:** warm bowed low notes remain the foundation, but
  spiccato/pizzicato eighths and a **3+3+2** cello response push against
  the kick while the reed bellows breathe.
- **Violin + glass:** expressive short-bow, upward replies, tiny sparkling
  glass subdivisions and contrasting longer phrases. The quiet half-time
  break leaves space for voice.
- **Drums:** clearer clap and hats, busier but controlled ghost notes,
  and a contrast between the straight pulse and the shadow rhythm.

The Film Club PULSE fader now begins at **58%** and SHADOW BEAT at **62%**
for a livelier opening groove. They control real local percussion; the
instrument changes are *MRT2 prompts*, not a claim that the native generator
creates five independent synchronized stems or a guaranteed exact timbre.
To hear them, use **UPDATE FILM CLUB SOUNDS SAFELY**. If Google MRT2
is already running, use **COPY 01–05** to edit its own prompt rows without
restarting or losing live audio. If the native host is idle, this can
start it with the new bank; Google may still require selecting `mrt2_small`.
No status message proves the model is audibly using the intended timbre. For independent editable layers
record short piano, cello and violin/glass PCM takes using the original
pedals, then arrange in Logic Pro. Short Z/X/C/V chord pickups against the
longer low cello foundation are a useful way to make it dance without
changing the master clock or copying any copyrighted melody.

## v0.9: interlocking beats, cleaner ethereal vocals, smaller interface

The three large Film Club panels in the rehearsal screenshots have been
removed from the visible surface: the big **Record the performance** box,
the oversized **Pyramid Afterimage** composition/audition box, and the
five large **0–60s storyboard / energy** cards. The original recording
engine and controls are **not deleted**: expand the compact
**RECORD SYSTEM AUDIO · LOGIC / OPTIONAL SCARLETT** item beneath the
header. The five actual MRT2 HEAR audition buttons and 2.4-second
native sustain slider are preserved in **INSTRUMENT AUDITION**,
collapsed by default. Gastown cue JSON remains in a small **ADVANCED**
drawer, and the real Film Club instrument/loop pedals remain below.

**Two actual interlocking rhythms share one 100 BPM, 4/4 clock.**
The main rhythm is a four-on-the-floor kick/backbeat and offbeat hats.
The second is a softer 3+3+2-inspired two-bar shadow pattern of synthesized
low tom, offbeat rim and metallic shimmer strokes. Adjust the two compact
faders marked **PULSE** and **SHADOW BEAT** independently. Neither starts
a second MIDI transport or doubles the kick; existing PCM recordings,
the native MRT2 generator, and the original Futureproof route stay on
their original timing. Shadow percussion is browser-only audio and is
**not** falsely claimed to be included in the original three-lane
drum-MIDI export. For Logic, capture the mixed system audio (or remake
the shadow layer as a separate percussion stem).

The Film Club **vocal texture** now defaults to a moderately wet
dotted-eighth echo (15%), low feedback (15%), darker airy tone (44%),
and lower live reverb (20%). Live Scarlett voice has a *wet-only* adaptive
gate (soft hysteresis, 200ms hold), 120 Hz input highpass, filtered
delay rumble rejection at 170 Hz, and a very quiet modulated doubling
chorus. This stops quiet mic/room noise from endlessly exciting
reverb/echo while allowing the **dry** headphone feed to retain natural
dynamic expression. Recorded vocal PCM stays dry and can be treated
non-destructively later in Logic. This is a broad shimmering
jazz-electronica sound design idea, not an imitation of a specific
artist's recording or vocal identity.

For monitoring: use closed-back headphones, turn off **Scarlett
direct monitoring** if Chrome is monitoring too, and avoid running
the VE-22's wet output *plus* heavy browser effects at the same time.
If the room/interface noise is stronger than your voice, lower physical
gain rather than increasing feedback; you can also turn TAPE ECHO OFF
and keep just the gated reverb/chorus. The original Emergency KILL VOCAL
FX button still works and does not remove saved audio clips.

## Recording the whole performance for Logic Pro

The Film Club UX retains the **original TOASTER full-set recorder**
directly below the top header, now in a **compact collapsed control**,
rather than the previous oversized always-open panel. This is the **same
existing full-set capture engine**, not a second recording engine or a
button that records only the browser drum bus.

In Chrome on macOS:

1. Expand **● RECORD SYSTEM AUDIO · LOGIC / OPTIONAL SCARLETT**,
   optionally check **Include Scarlett / VE-22 voice**.
2. Click **● RECORD FULL SET**. This user-initiated click is what makes
   Chrome ask for screen-sharing permission. Nothing should ask for
   screen access merely from opening the page.
3. In Chrome's picker choose **Entire Screen** and **Share system audio**.
   The browser refuses to start recording if it cannot access a system
   audio track; this protects against misleading files without Google MRT2.
4. Make a sound and check the level/status: **MAC AUDIO VERIFIED**.
5. Perform your music, then select **■ STOP & SAVE AUDIO**. The stereo
   recording downloads as M4A when supported, or WebM otherwise.
6. Drag the M4A into a **100 BPM / 4⁄4** Logic Pro project, or convert
   WebM to WAV first. For true individual mix stems, record your
   instrument lanes separately; this is a stereo system-mix recording.

The recorder's buttons retain their original `setRecordStart`,
`setRecordStop`, `setRecordMic` and `setRecordStatus` IDs and
behaviour. Its device and permission errors remain handled by the
original source. The Futureproof `/toaster/live` UX still defaults
to the collapsed ADVANCED recorder.

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

## v0.8: four playable Accelerando chords, not just labels

Film Club's Pyramid deck has been revoiced as a four-pad performance bank,
**Z = Em, X = E7, C = Am, V = E**. These play real 4-note MIDI voicings:

| Pad | MIDI notes | Warm cello/harmonium bass register |
| --- | --- | --- |
| Z · Em | E3 G3 B3 E4 (52,55,59,64) | E2 G2 B2 E3 |
| X · E7 | E3 G♯3 B3 D4 (52,56,59,62) | E2 G♯2 B2 D3 |
| C · Am | A3 C4 E4 A4 (57,60,64,69) | A2 C3 E3 A3 |
| V · E | E3 G♯3 B3 E4 (52,56,59,64) | E2 G♯2 B2 E3 |

The render-only film variant updates the source's onscreen pads, virtual
keyboard shortcuts, MIDI event names/notes, native role chord pads, loop
replay, and **Swift `harmony:"accelerando"` chord overrides** together.
The cello/harmonium still receives a -12 semitone octave, the piano
does not. Futureproof's original version is not rewritten.
Old recorded MIDI clips are interpreted under the currently displayed
four-chord bank; native PCM takes are audio and not automatically
reharmonized. **Export earlier takes before a new recording session** if
you need to preserve their original pitches.

This is an independently played arrangement, not a copied vocal,
melody or sampled track.

## v0.7: restore the Pyramid low cello + harmonium foundation

The original Futureproof piece got its warmth from **low bowed cello
and a softly breathing harmonium drone**, with suspended piano above it.
This Film Club variation now brings that specific foundation back instead
of asking a generic cello/upright-bass prompt to cover the whole low end.

- **Prompt 01:** recognisable *acoustic grand piano* with wooden
  soundboard, felt-hammer attack, piano strings, suspended F♯ / Gmaj7 /
  A6 extensions and long decay. Explicitly excludes synth, organ and
  electric-piano timbres from the piano role.
- **Prompt 02:** low expressive bowed cello *doubled by warm reed-organ
  harmonium*, a continuous F♯ bass drone, slow moving low octave,
  woody resonance and connected expressive arco notes.
- **Real lower MIDI register:** only on this Film Club page, the cello
  **HEAR** audition, its visible chord pads and Z/X/C performance chords
  are sent an octave lower. F♯3 becomes F♯2, Gmaj7 and A6 keep their
  voicings shifted by -12 semitones. The standard piano, strings,
  glass and original Futureproof page all retain their normal voicings.
- **Loop playback:** recorded cello texture MIDI events also apply the
  Film Club low octave; independent existing PCM clips are left alone.

There is still one native generative MRT2 Audio Unit with five weighted
prompts, so this does not magically split harmonium and cello into
separate simultaneous generators. It steers the same cello/harmonium
timbre through a truly low, warm harmonic register, then lets you
record that sustained sound as its own PCM loop. For additional bass in
the final arrangement, use the existing **CELLO** saved-loop channel
fader, rather than boosting the entire master including kick.

The revised prompt text needs applying to Google's actual AU bank.
Save any valuable takes before a prompt restart; changing the prompt
does not rewrite recordings already captured.

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

### Non-destructive Google MRT2 prompt workflow (Film Club)

This fixes a real failure: the old green `APPLY FILM CLUB SOUNDS TO MRT2`
button stopped a **playing** Audio Unit, closed its selected Google
model window, then attempted to restart it. In the Google-UI model mode
that new instance may not have a selected model, so the AI went silent.
The new Film-only control **never sends `stop` to the native host**.

1. **When MRT2 is already playing:** click **UPDATE FILM CLUB SOUNDS
   SAFELY**. It reveals the five **COPY 01–05** buttons and leaves
   Google playing, including its current native memory loops.
2. Copy prompt 01, paste it into Google's **existing** first prompt row,
   then press Enter to confirm. Repeat for 02 cello, 03 violin,
   04 glass and 05 drums. These are real text edits inside Google's own
   running Audio Unit, not edits to the memory banks or browser-only labels.
3. The new **OPEN CURRENT GOOGLE PROMPT WINDOW · NO RESTART** action can
   bring forward an existing Google model-picker window. If the AU is in
   bookmark mode or has not finished loading, this action **refuses to
   switch modes**, precisely because doing so could destroy running audio.
   If the Google popup is already open, you can simply use it directly.
4. If native MRT2 is **idle**, the same Update button may issue one
   `start` request with all five Film Club strings. It never stops an
   active model, calls a second start during initialization, or retries
   blindly when the status endpoint is unavailable. Selecting
   `mrt2_small` in Google's own window may still be needed.
5. Audition the actual sound. A match in Google's serialized
   `MGRT_Prompts` is useful evidence of saved text, but not proof its
   MusicCoCa embeddings or audio output were updated.

Film Club also captures the old expanded TOASTER **APPLY PROMPTS** /
**APPLY DRUM PROMPT** buttons and routes them through this same safe
flow, rather than letting the shared legacy stop/start handler run. The
original `/toaster/live` Futureproof workflow is unchanged.

The browser **cannot automatically type into Google's separate AUv3
window**. Google owns that editor, so a true in-place prompt update
currently requires the official UI. This PR makes that path accessible
without destroying a working model, and distinguishes AU saved text from
the Swift host's desired text. If Google now matches the five Film prompts
while the Swift host still reports Futureproof strings, the status reports
the AU match instead of misleadingly calling the prompts old.

### Troubleshooting a silent or stale model

Check that Google actually has `mrt2_small` loaded and its transport is
playing; choose a live MIDI note in the AU window. If the editor shows
the old text, use COPY 01–05 in the current window without closing the
AU. If the native host says it is initializing, allow initialization to
finish; don't start a second generator. If **OPEN CURRENT GOOGLE PROMPT
WINDOW** refuses to open, this means the current host is not safely in
Google's UI mode, not that the new prompts were installed. To deliberately
change loading modes, export native takes first and use the original
model-selector controls separately from this safe prompt workflow.

This is not a claim that the underlying installed Google plugin has
been modified. The safe editor action requires rebuilding the Swift
companion when testing the PR on Mac:

```bash
cd ~/Projects/suzy-ai
git fetch origin
git switch fix/film-club-nondestructive-google-mrt2-prompts
git pull --ff-only
bash scripts/build-toaster-magenta.sh
.venv-mac/bin/python -m suzy_ai.music.magenta_stage
```

The live page remains `http://127.0.0.1:7345/film-club/soft-reset/`.
Stop the old stage with Ctrl+C before launching the new code. Unlike
pressing the old Apply button, browsing to this view doesn't reconfigure
the native model.

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
Magenta Audio Unit. Browser prompt text does not automatically change a
playing Google model. Film Club now uses safe in-place edits in Google's
own prompt editor when audio is running; Futureproof retains its original
prompt workflow. No independent model or silent automatic hot-swap is
claimed. Export takes before any deliberately chosen model restart.

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
