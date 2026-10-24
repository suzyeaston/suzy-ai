# SUZY//AI / Futureproof: the 1990s hip-hop, jazz-rap and R&B knowledge lab

## Goal: the musician is the artist

Suzy performs her own **1990s hip-hop/R&B** music with Logic beats and
live vocal loops. Local Qwen is an optional **bandmate** proposing *new*
music in response to her sung phrases and arrangement, NOT an Erykah Badu
impersonator or a generator of Nas tracks. Qwen has no direct audio hearing:
phrase/rhythm analysis must produce structured input separately.

## What this PR does and DOES NOT do

The small, attributed `suzy_ai.music.era_knowledge` corpus contains **five
starter reference packs** and nine original arrangement exercises. A lexical
retriever selects at most three (up to five) short cards with clickable source
provenance and an explicit warning that its `proposed_action` is our creative
interpretation, not the recorded artist's MIDI. Everything runs offline with
Python's standard library; no internet is queried during the rehearsal.

This **does not** train or fine-tune Qwen, feed it during the live show, make it
hear the beat, or reproduce the album recordings. It is an explicit staging
step for a model-grounded composer and falsifiable A/B tests.

## Source-backed reference packs

### 1. Nas / Illmatic (1994)

**History:** Nas's 1994 Queensbridge debut features productions by DJ Premier,
Large Professor, Pete Rock, Q-Tip and L.E.S. It is a record of lyrical
storytelling, producer interplay and jazz-influenced hip-hop, embedded in its
specific New York social context.

**Sources:** [Library of Congress album essay](https://www.loc.gov/static/programs/national-recording-preservation-board/documents/Illmatic_McDuffie.pdf),
[Nas: Time Is Illmatic documentary press kit](https://d13jj08vfqimqg.cloudfront.net/uploads/release/press_kit/95/Nas_TII_PressKit.pdf).

**Our musical exercise:** make an ORIGINAL two-note piano motif; repeat with
one interval variation, keep space for Suzy's sung or rapped line and a
steady boom-bap skeleton. `Illmatic` is a reference, not a BPM preset or a
style-transfer license. No Nas lyrics, melodies or sample chops are included.

### 2. Erykah Badu / Baduizm (1997)

**History:** Badu identifies raw underground hip-hop in her early demos and
describes developing music with Questlove, James Poyser and the Roots. Her
1997 debut joins R&B vocal delivery, jazz conversation and hip-hop production.

**Sources:** [Erykah Badu's Essence interview](https://www.essence.com/entertainment/erykah-badu-baduizm-25-years/),
[Red Bull Music Academy interview](https://www.redbullmusicacademy.com/lectures/erykah-badu-frother-of-the-month/).

**Our musical exercise:** a newly composed answering phrase after the lead
voice finishes; warm electric keys with a held tone; enough unplayed space
for vocal breathing. The synthesizer must not pretend to reproduce Badu's
recorded voice.

### 3. A Tribe Called Quest / The Low End Theory (1991)

**History:** The Library of Congress documents its Native Tongues connections,
jazz influences, bass focus and intentionally spare musical frameworks.

**Source:** [Library of Congress album essay](https://lcweb2.loc.gov/static/programs/national-recording-preservation-board/documents/The-Low-End-Theory_Amorosi.pdf).

**Our musical exercise:** make the bass a second voice; answer a sung line with
a short root/passing-tone gesture, not a busy wall of extra instruments.

### 4. D'Angelo / Brown Sugar (1995)

**History:** A bridge of soul instrumentation, keyboard playing and hip-hop
production, documented and musically discussed in an expert jazz podcast.

**Source:** [You'll Hear It: album analysis](https://youllhearit.com/episodes/brown-sugar-dangelo/transcript)
(interpretive secondary musical commentary).

**Our musical exercise:** choose a soft keyboard answer after the vocal line;
try contrasting lengths and guide tones, using your own voicings.

### 5. Lauryn Hill / The Miseducation of Lauryn Hill (1998)

**History:** Her music put singing and rapping in dialogue with live instruments
and human performance texture. The album and its collaborators belong in the
history, not just a catch-all neo-soul tag.

**Sources:** [1999 Biography Today profile](https://files.eric.ed.gov/fulltext/ED439044.pdf),
[BET retrospective](https://www.bet.com/hip-hop-awards/articles/7uq9da/the-miseducation-of-lauryn-hill-turns-25-how-a-classic-debut-galvanized-a-generation-of-black-women-and-changed-hip-hop).

**Our musical exercise:** give dense rap-like phrasing its own uninterrupted
space and answer with a held sung note afterward.

### A note on chronology

Badu's *Mama's Gun* (2000) and D'Angelo's *Voodoo* (2000) are important
related references but NOT 1990s records. They can be added as a separately
labeled follow-on research set.

## Local inspection

From repo root:

```bash
python3 -m unittest discover -s tests -p 'test_era_knowledge.py' -v
python3 -m suzy_ai.music.knowledge_probe \
  --query "Illmatic boom bap jazz piano, leave room for my R&B voice"
python3 -m suzy_ai.music.knowledge_probe \
  --query "Baduizm jazz soul vocal call response"
```

The output lists the exact reference, exercise and URL that *could* be given
to Qwen. Unknown topics return an empty list, NOT invented history. The corpus
contains original analysis, not source article text or audio, and does not
modify artist-approved private teachings.

## How we will know Qwen actually benefits (next PR)

A reproducible three-way A/B bench should use the **same** 4-bar musical
input and locally hosted Qwen3-1.7B GGUF:
1. **Baseline:** no era knowledge; require valid new MIDI note events.
2. **Grounded:** identical prompt with the retrieved 1–3 knowledge cards.
3. **Shuffled/wrong cards:** supply irrelevant era references as a negative control.

Report: selected sources, Qwen model identifier, exact JSON note output,
schema validity, distinctness from lead line, musicians' blind preference
and inference latency; never present synthetic/mock model responses as proof.
A cultural knowledge gain exists only if human musical assessment improves
and Qwen clearly uses the relevant information. Ordinary prompts alone
cannot prove genre competence, and a familiar phrase may still sound generic.

## Rights and attribution

This repo contains **no** commercial audio, samples, MIDI transcriptions,
copyrighted lyrics, synthesized celebrity voice, album art, or scraped
article text. Research links are provided for human inspection, not as proof
that downstream copyrighted recordings may be sampled. Build musical practice
from ideas, own-made beats, your voice and properly licensed MIDI/audio. Keep
citations, distinguish historical claims from our own production exercises,
and seek permission before using protected samples in a public performance.
