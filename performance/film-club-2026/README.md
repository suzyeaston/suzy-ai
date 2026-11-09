# SOFT RESET / Make Art Not War / SUZY//AI

**An original one-minute audiovisual composition by Suzy Easton.**
For the November 12, 2026 BC + AI Film Club screening.

## Why this lives here

This is a **new song** inside `suzy-ai`, not a replacement for the Futureproof
`PYRAMID ORBIT` looping performance. Its browser interface preserves the
performer-led, overlapping loop idea, with a switchable **Pyramid Orbit chord
palette**. It does **not** bundle Radiohead audio, reproduce the original
performance recording, or overwrite its saved clips.

The sound engine is deterministic Web Audio. It creates actual stereo audio
with oscillator and noise instruments, not a pretend player. Genuine Google
Magenta RT2 audio is available **only if you render/record it separately and
import the file**. Imported voice, guitar, or Logic takes work the same way.
The app neither starts the AI model nor claims symbolic notes are AI audio.

## Run and audition on your Mac

From your `suzy-ai` checkout:

```bash
git pull --ff-only
python3 -m http.server 8787 --bind 127.0.0.1
```

Open **http://127.0.0.1:8787/performance/film-club-2026/** in Chrome.
Headphones recommended. Click **PLAY FILM SCORE** to unlock browser audio.

Alternatively, when the existing native Magenta stage is running from this
checkout, open **http://127.0.0.1:7345/film-club/soft-reset/**. Your
**original** Pyramid environment stays at
**http://127.0.0.1:7345/toaster/live**.

If you are auditing the feature branch before merging, check out
`feat/film-club-soft-reset-v01` first; `git pull` on `main` does not
include unmerged changes.

### First musician test

1. Play once at **low volume**. Listen for the harbour pulse (0–10s),
   accelerating percussion (10–24s), metallic dissonance (24–38s), expressive
   human entry (38–48s), and soft reset (48–60s).
2. Click each of five scene blocks. Transport jumps to the corresponding
   exact second. Try `SOFT RESET` and `PYRAMID ORBIT` harmonic palettes.
3. Balance the lanes, then mute the metal track. The song should become less
   threatening without changing tempo.
4. Click **ARM OVERDUB**, press **A S D F G** during playback, then disarm.
   Notes are quantized to the nearest eighth-beat and return at the same
   places on the **next** 60-second cycle.
5. Optionally import **your own** actual Magenta, Logic, guitar or vocal
   render. It will loop for the film duration. The browser does not upload it.
6. Export `soft-reset-60s-master.wav`, then audition the file outside the
   browser (quickly inspect its first seconds and full ending). Export
   `soft-reset-gastown-cues.json` for timed visual editing.

All clips and overdubs are **memory-only in v0.1**. Export the WAV and cue
JSON before closing the tab. The app does not record your microphone in this
iteration; a vocal recording must be imported. No network, cloud account,
Logic, or neural model is needed for the included sound.

## Compositional map

| Film time | Composition | Gastown visual treatment |
| --- | --- | --- |
| 0–10s | Harbour sub, glass, suspended strings, very restrained pulse | Grounded Waterfront/Gastown ambience |
| 10–24s | Gradual BPM rise, repeating notes, hats, tightening bass | Traffic and lights accelerating |
| 24–38s | Industrial percussion, metallic dissonance and density | Machine conflict, abstraction, unstable image |
| 38–48s | Abrupt slowdown, human melodic intervention | Performance interrupts machinery |
| 48–60s | Harmony opens, groove returns without violence | City becomes an instrument: MAKE ART NOT WAR |

The song is an *original* response to the idea of cultural accelerando, not
a Grimes cover or sound-alike request. The previous conversation's
**"SOFT RESET"** story arc is the narrative source.

## Gastown Simulator handoff

The cue JSON uses `suzy-film-cues/v1`. Each cue includes `time_sec`,
`end_sec`, `scene`, `visual_event`, `intensity`, `treatment`, and
`harmony_hint`. All cue times are in **absolute soundtrack seconds**.
It also includes tempo snapshots, overdub timing and whether imported audio
was present. Imported audio bytes are **not** embedded in JSON.

This is an **edit handoff**, not an automatic simulator control protocol yet.
Line up screen recordings or rendered clips with the 60-second WAV in your
video editor. The original source of truth for film timing is 60.000 seconds.
No direct game-world state or simulator source files are changed.

## Test

```bash
node --test tests/film_club_soft_reset.test.cjs
python3 -m unittest tests.test_soft_reset_stage
```

These cover score determinism and time windows, accelerando, sample PCM
encoding, Web Audio graph construction, module contracts, fixed localhost
routes, and preservation of the Pyramid route. CI additionally runs
`bash scripts/test-film-club-browser.sh` on Ubuntu Chrome to verify that
the real 60-second OfflineAudioContext render contains audible (non-silent)
PCM in every editorial scene without full-scale clipping. CI still does not
prove that the mix *sounds good* or that screen capture records system audio.
Human listening and a local exported-WAV check are still needed.

## v0.2 candidates after listening

A microphone capture lane with correctly aligned audio overdubs; a playable
guitar/piano MIDI input; live Magenta AU input routed as real captured PCM;
scene-controlled harmonic and rhythmic changes; and a versioned
Gastown-Simulator cue importer for synchronization. Do not make the
simulator and browser transports both pretend to be the master clock.
