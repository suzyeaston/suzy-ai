# Evidence-backed 1990s hip-hop / R&B cards for local Qwen

This PR turns **the supplied deep-research report** into a small, inspectable,
**offline** research card set. It supplements the existing 1990s starter
packs from PR #33 and the Rascalz pack from PR #36. Suzy is the HUMAN artist
performing prepared 1990s-inspired beats and live vocals; Qwen is an
optional, original accompanist. It is not an imitation of Nas, Erykah Badu
or Rascalz.

## Twelve structured cards

Each of six records has two curated starter cards:
- Nas / *Illmatic* (1994): **gap replies** around dense vocal phrasing,
  and **contrasting producer/section roles**.
- Erykah Badu / *Baduizm* (1997): **call-and-response space**, plus the
  **Philadelphia/Roots vs Mama's Gun (2000) chronology boundary**.
- A Tribe Called Quest / *The Low End Theory* (1991): **bass-first arrangement**
  and **separate register budgets**.
- D'Angelo / *Brown Sugar* (1995): **original keys with compact voice leading**
  and **foregrounding the singer's existing arrangements**. Do not assign
  Voodoo's (2000) displaced-drum history to Brown Sugar.
- Lauryn Hill / *The Miseducation of Lauryn Hill* (1998):
  **rap/sung phrase-density response** and **human performance timing**.
  Original liner credits and the later New Ark dispute remain distinct.
- Rascalz / *Cash Crop* (1997): **Vancouver MC/DJ section roles** and
  **space for the next singer/MC entry**. Northern Touch's 1998 single
  and later-album appearance must NOT be presented as an original 1997 track.

Every card records its individual ID, album, exact evidence URL, author,
date, source type, a narrowly supported historical proposition, a SEPARATE
original compositional action, controls, sample hypothetical constraints,
tags and uncertainty. A listening hypothesis is not promoted to a proven
transcribed groove. No artist samples, protected melodies, stems, lyrics,
track MIDI or unlicensed drum breaks are included.

**Caution:** Metadata and source summaries were translated from the research
report. Some individual historical source statements still require a
separate line-by-line primary-source verification. The URLs are bibliographic
references and are NEVER downloaded by the live model.

## Source / model boundary

The new `research_cards.research_brief()` is a deterministic *local*
text retriever. It returns at most two small cited cards by default,
and no card for unknown subjects. Retrieval is opt-in; the original
`knowledge_brief()`, existing artist-approved private music teachings
and previous live-vocal behavior are unchanged.

On a separate non-realtime worker, `LocalQwenComposer` can now send these
cards to the already running localhost `/v1/chat` Qwen endpoint via the
new `use_deep_research=True` API or `--with-deep-research` CLI flag.
It requires strict, bounded, ORIGINAL note tuples and an optional
`used_reference` matching one of the supplied individual card IDs.
The existing `use_memory:false` + empty chat history remain unchanged.
No audio waveform is uploaded and model weights never change.

### Inspect knowledge without running a model

```bash
cd ~/Projects/suzy-ai
python3 -m suzy_ai.music.research_probe \
  --query "Rascalz Cash Crop Vancouver vocal space"
python3 -m suzy_ai.music.research_probe \
  --query "Baduizm R&B vocal call response"
python3 -m unittest discover -s tests -p 'test_research_cards.py' -v
```

### Do A/B with the real LOCAL Qwen (synthetic lead only)

Requires your local Qwen core already listening at `127.0.0.1:7332`.

```bash
# A: no research card
.venv-mac/bin/python -m suzy_ai.music.qwen_composer \
  --query "Baduizm R&B vocal reply" \
  --wav /tmp/suzy-research-A.wav

# B: same hand-authored test melody and instruction, with cited card retrieval
.venv-mac/bin/python -m suzy_ai.music.qwen_composer \
  --query "Baduizm R&B vocal reply" \
  --with-deep-research --wav /tmp/suzy-research-B.wav
```

The outputs are quiet audition WAVs of Qwen-selected pitches and durations;
import both into the same Logic session and judge blindly. Responses can
differ due to random decoding, so a single A/B run is **not proof** that
the research helps. The Qwen model file, version, memory load, actual
latency and music quality have NOT been measured in this PR.

**Next evaluation PR:** add a reproducible A/B/C runner using baseline,
relevant and irrelevant-but-token-matched cards with identical input and
recorded local inference settings, plus metrics for vocal-rest overlap,
novelty, latency and blind listener ratings. The user's report proposes
3 original clips x 3 conditions x 5 seeds = 45 model calls. The current
CLI does NOT implement or claim that evaluation. Actual Logic performance
routing remains a separate, opt-in task.

## Rights, facts and musician agency

- The distinction between documentary history and musical design is explicit.
- Numeric timing/rest/note constraints are hypothetical test values, NEVER
  measured album transcriptions.
- Public research cards are not silently promoted to `live_use:true` private
  artist-approved memory.
- If Qwen fails or times out, Suzy's Logic beats and existing live looping
  must keep playing independently.
- This path is purely offline audition/analysis. It must NOT be wired into
  an October 29 stage route without real Mac memory/audio tests and approval.
