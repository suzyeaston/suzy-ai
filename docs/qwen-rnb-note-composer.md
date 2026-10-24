# Local Qwen: original 90s hip-hop/R&B phrase answers (experimental)

This is the first **model-generated note-event** path in SUZY//AI.
Suzy is the musician: her own Logic beats and vocals are the foundation.
Local Qwen composes one short proposed response *after* a phrase has been
captured; it does not perform her persona or imitate Nas or Erykah Badu.

## Technical contract

1. Existing offline phrase extractor supplies approximate monophonic note
   events, duration and **performer-supplied** BPM.
2. Optionally retrieve at most 3 cited **1990s research cards** from
   `era_knowledge.knowledge_brief`. This is **not Qwen training**, and it is
   separate from the private artist-approved world model.
3. Send compact JSON as a text prompt to the existing localhost Qwen
   `/v1/chat` endpoint (default `127.0.0.1:7332`). Explicit
   `use_memory:false`, no history, no PCM/audio, 256-token request budget.
4. Qwen generates ORIGINAL note events: MIDI pitch, start beats, duration
   beats, velocity, and an optional provenance ID from the supplied cards.
5. Strict schema/time/range validation. No repeat-the-lead note sequence,
   no arbitrary JSON or unsupplied citations, and no fallback that pretends
   to be a successful model generation.
6. Only if explicitly asked, render a **quiet audition WAV** using the
   already-merged counterline synthesizer. This does not route into Logic.

All reasoning happens outside any audio callback. The API has an eight-second
maximum timeout, but **actual latency on the user's Mac is unknown**.
Any slow, failed or irrelevant answer can be ignored without touching the
original loop.

## Run a safe test on your Mac

With SUZY//AI's existing local Qwen service available on port 7332:

```bash
cd ~/Projects/suzy-ai
git pull --ff-only
.venv-mac/bin/python -m unittest discover -s tests -p test_qwen_composer.py -v

# No microphone, speaker, MIDI, or file output:
.venv-mac/bin/python -m suzy_ai.music.qwen_composer \
  --query "Illmatic-influenced sparse boom bap, original R&B vocal answer"

# Compare with the retrieved source-backed knowledge:
.venv-mac/bin/python -m suzy_ai.music.qwen_composer \
  --query "Illmatic-influenced sparse boom bap, original R&B vocal answer" \
  --with-knowledge

# OPTIONAL: physically audition a newly composed Qwen note phrase:
.venv-mac/bin/python -m suzy_ai.music.qwen_composer \
  --query "Baduizm-informed airy R&B answer with one held tone" \
  --with-knowledge --wav /tmp/suzy-qwen-rnb-test.wav
```

Demo uses a hand-authored synthetic lead phrase, not a recorded commercial
album or a live microphone. It is a no-gear first validation of a genuine
local-model inference. Generated JSON is inspectable; the CLI prints selected
reference IDs so users can verify what material reached the prompt.
**A model claiming it used a reference does NOT prove musical understanding.**

## Research/evaluation PR after this

Run same measured lead + same prepared Logic beat under:
- A: Qwen **without** research cards.
- B: Qwen **with** relevant Illmatic/Baduizm/jazz-rap cards.
- C: Qwen **with irrelevant cards** (negative control).

Keep temperature / model settings controlled, record actual Qwen outputs,
JSON rejection rate, inference latency, groove fit, human listener preference,
and whether the generated notes are genuinely distinct from the singer.
There is no hardcoded famous melody or sampled drum break in these tests.

For the October 29 Futureproof performance, this model path remains
**offline audition only**, not a live dependency. Make actual Logic routing
a separate PR after measuring timing, failure behavior and safe mute/stop on
the user's 8 GB Mac.
