# SUZY//AI: stop judging two sine notes in isolation

## Why the previous A/B experiment was misleading

The prior Qwen composer CLI **always used a synthetic three-note lead**
(C4 E4 G4), **had no backing track**, **had no chord information**, and
showed the model a two-note JSON example. The renderer played just Qwen's
small sine-wave note phrase, separate from Suzy's beat and voice.

The result "two notes with no audible A/B difference" is entirely
consistent with this underconditioned demonstration. More album facts in
the prompt are not equivalent to musical training or proof of knowledge.

### What this PR changes

- Removes the two-note literal from the model's instruction; explicitly
  distinguishes a deliberate 1–3 note sparse answer from a possible
  4–8 note active counterline. No arbitrary minimum note-count is imposed.
- Adds **optional, validated actual groove context** to
  `LocalQwenComposer(accompaniment=...)`, separate from cultural cards.
- Introduces `suzy_ai.music.listening_lab`, an explicit offline tool to
  read **your OWN 1.5–8-second voice and beat WAV exports**, detect an
  approximate melody from voice, and compute a simple half-beat RMS energy
  grid from the beat. The user supplies Logic BPM and an optional chord
  symbol. The two sources must be frame-aligned PCM16 WAVs at 44.1/48kHz.
- Compares A (no cultural research) vs B (relevant deep-research cards)
  **with the same actual lead, backing, instructions and local Qwen**
  and writes two preview WAVs containing identical beat and vocal tracks
  with only Qwen's proposed answer differing.
- Prints the **exact note events**, reference IDs delivered and claimed,
  count of detected lead notes, energy grid and an
  `identical_note_events` boolean. Does not pretend small differences
  or references prove cultural learning.
- Uses conservative fixed gains to avoid accidental loud preview output.
  No cloud endpoint, stage-audio callback, voice cloning, samples or
  changes to Logic/live looper. All inference is localhost and off-thread.

## Preparation in Logic

1. Set a tempo you actually use in your R&B song, perhaps 90–95 BPM.
2. Export **the same selected 1.5–8 sec region**, once with ONLY your
   vocal and once with ONLY the beat. Both files MUST have the same
   exact duration and sample rate, at PCM 16-bit 44.1kHz or 48kHz.
   Mute plugins that make the voice polyphonic while testing the
   monophonic pitch extractor. The Bosss VE-22 may confuse note tracking;
   dry vocals are preferable for initial QA.
3. No rhythm samples from Rascalz/Nas/Badu are required or included.
4. Keep Qwen's original server running locally at port 7332.

## Rehearsal A/B

```bash
cd ~/Projects/suzy-ai
git pull --ff-only

.venv-mac/bin/python -m unittest discover -s tests -p test_listening_lab.py -v

.venv-mac/bin/python -m suzy_ai.music.listening_lab \
  --voice-wav ~/Music/suzy-voice.wav \
  --beat-wav ~/Music/suzy-beat.wav \
  --bpm 92 \
  --chord Am9 \
  --query "Baduizm vocal space and Rascalz Cash Crop bass-first conversation" \
  --out-dir ~/Music/suzy-ai-listening-test
```

Output directory contains:
- `A_no_research.wav`: original beat + lead + Qwen notes without cards.
- `B_with_research.wav`: same beat + lead + Qwen notes with up to two
   relevant sourced cards.
- `comparison.json`: measured features, exact notes, provenance and
   whether A and B are MIDI-identical.

**If `identical_note_events=true`, report that the A/B generated identical
notes.** Two separate calls may differ because of sampling randomness.
Even if they differ, only human audition can tell whether B improves.

Import both WAVs in Logic at the SAME timestamp and compare. Our preview
uses the existing plain sine synthesizer, so it still cannot reproduce
a Rhodes, bass, sampler or convincing vocal-part timbre. A/B is currently
an *experiment*, not a genre learning score.

## Critical limitations

- This is NOT direct machine audition of your beat. The rhythm
  measurement is only normalized RMS per half beat; Qwen receives no
  raw audio, snare/kick identification, microtiming, key detection, or
  symbolic chord transcription.
- The `--chord` symbol is supplied by Suzy and **not validated against
  what is sounding**. If missing, musical harmony is unknown. The
  validator checks its safe shape only.
- Existing extraction can return inaccurate or no notes for polyphonic
  singing, vibrato, noise or VE-22 output; this is not a transcription
  or singer identification product.
- The previous response is limited to max eight notes, no polyphony,
  and only eight seconds of source. 1.7B Qwen may still return very
  sparse answers, malformed JSON, or identical notes.
- It is not valid to claim this experiment "taught Qwen" the music.
  Real musical education needs a separate TRAINING/EVALUATION set:
  rights-cleared recorded groove examples with accurate transcribed
  onset/velocity features, human-scored original arrangements,
  held-out tunes and repeated tests. The factual research corpus is
  a relevant cultural reference, not learned musical ear.
- A and B do not have a controlled seed through the current
  `/v1/chat` transport. This is a quick paired listening smoke test,
  NOT the report's preregistered 45-run A/B/C benchmark.
- The 8 GB Mac's local Qwen latency and simultaneous Logic load remain
  unmeasured. **This experiment must not become a required stage
  audio path**. If anything fails, Suzy's prepared Logic music continues.

## Development direction

The next major ability is richer musical conditioning: beat-event
(onsets/swing/velocity) estimation, performer-confirmed chords or
Logic MIDI import, multi-bar harmonic voice leading, and learning from
Suzy's accepted/rejected responses. Preserve the historical research and
Rascalz/Illmatic/Baduizm source fidelity, but measure *music* rather than
counting source-card IDs or prompt words.
