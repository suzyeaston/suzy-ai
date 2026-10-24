# Deep Research brief: real 1990s hip-hop / neo-soul knowledge for SUZY//AI

## Assignment

Research the documented production, musical arrangements, and cultural
lineages of 1990s East Coast hip-hop, jazz-rap and hip-hop-rooted R&B.
**The human performer, Suzy, is the 90s-inspired artist.** She performs
her own prepared Logic Pro beats, vocals and loops. A local Qwen3 1.7B GGUF
on an 8 GB Apple Silicon Mac is to be a responsive, *original* musical
accompanist, not an imitation of Nas, Erykah Badu or another artist.

## Priority sources

1. Nas, *Illmatic* (1994): NYC/Queensbridge contexts, DJ Premier, Q-Tip,
   Pete Rock, Large Professor and L.E.S.; production differences among
   tracks, jazz-record production practices, space for a densely phrased MC.
2. Erykah Badu, *Baduizm* (1997): actual collaborators, her explicitly
   described underground-hip-hop demo roots, Roots/Questlove/James Poyser
   sessions, call-and-response, phrasing and keyboard/bass relationships.
3. A Tribe Called Quest, *The Low End Theory* (1991): Native Tongues,
   jazz sampling context, sparse arrangements and bass as the centre.
4. D'Angelo, *Brown Sugar* (1995): hip-hop-soul crossover, instrumentation,
   keyboard voicing and arrangement without conflating with *Voodoo* (2000).
5. Lauryn Hill, *The Miseducation of Lauryn Hill* (1998): sung and rapped
   lines, collaborative credits, live instrumentation, and preservation
   of musical texture and human imperfections.
6. Optional cross-links: Gang Starr and DJ Premier, Pete Rock & C.L. Smooth,
   De La Soul, Digable Planets, The Roots, Mary J. Blige, Maxwell.
   Respect the records' dates; label *Mama's Gun* and *Voodoo* as 2000.

## Research rules

- Use musician/producer interviews, primary interviews, verified liner
  notes/credits, archives, musicological analyses, peer-reviewed studies,
  credible historical journalism, and accurate album release metadata.
- Every factual historical claim needs an author, title, year/date, URL and
  exactly what it supports. Distinguish firsthand testimony from critic
  analysis and hypothetical musical design.
- Do not claim to know exact BPM, drum timing, sample clearance, chords,
  melody notes or production equipment without a cited source or legal
  audio/MIDI analysis. Never invent transcriptions.
- Place these cultural traditions in their social and Black American
  musical histories, not merely a "dusty sample" aesthetic shorthand.
- Don't output lyrics, copied melodies, recognizable drum breaks,
  audio samples, unauthorized stems, or unlicensed transcribed MIDI.
- Record contradictory claims and uncertainty. Keep exact song names,
  timeline and personnel accurate.

## For EACH reference produce a structured mini-dossier

- Historical overview in 150-250 new words with 3+ traceable references.
- Production team and specific documented musical influences.
- **Listening hypotheses**, clearly labeled interpretation, about pocket,
  groove, rhythmic density, bass interaction, jazz harmony, space and
  voice/MC phrasing. Don't mistake subjective analysis for measured data.
- Three original, rights-safe SUZY//AI arrangement exercises that could
  be generated algorithmically from *Suzy's* input, not recreated from
  copyrighted notes; each exercise has an observable effect.
- A lightweight numerical/music representation: beat positions,
  rests, MIDI note ranges, durations, velocities and possible chord
  tensions. Example numbers must be labeled ORIGINAL hypothetical MIDI.
- Citations attached to claims, and one independent alternative source
  for any contested technical detail.

## Output schema for the local knowledge engine

For each exercise include:
```json
{
  "reference_id": "illmatic-1994",
  "source": {
    "title": "Source title",
    "author": "Byline / institution",
    "url": "https://...",
    "date": "YYYY or YYYY-MM-DD",
    "supports": "Narrow historical claim verified in source"
  },
  "historical_claim": "A narrow evidenced fact",
  "original_musical_idea": {
    "cue": "short 1990s boom-bap arrangement",
    "role": "vocal_reply",
    "action": "Create a short answering melody after the vocalist rests",
    "controls": ["rest_beats", "pitch_events", "duration_beats"],
    "observable_test": "Same lead, less overlap in response"
  },
  "rights": "new arrangement suggestion, no copied audio/MIDI",
  "uncertainty": "Which details require musical listening verification"
}
```

No inference-generated historical claim should be automatically marked
artist-approved. The public reference corpus and user's private
`live_use:true` teachings remain separate.

## Musical intelligence experiment

Take three **original** user-created 4-bar backing clips (e.g. 85/92/100 BPM)
and three matching lead-vocal phrases, or clearly labeled synthetic
MIDI stand-ins if actual recordings aren't available. Run the **same**
local Qwen model, same temperature, same input and 3 conditions:

A. Baseline: no research cards.
B. Relevant: retrieve the correct evidence-backed card(s).
C. Negative control: irrelevant references, with no access to correct cards.

Capture: card IDs actually delivered, model JSON, model name/version,
token/time budget, valid-note %, no-overlap %, melodic novelty (not exact
lead copy), and whether the singer has room at the next entry.
Present randomized anonymized audio exports to Suzy for 1-5 ratings of
pocket, harmonic fit, responsiveness, originality and musical interest.
Repeat enough cases to avoid calling a single lucky completion proof.

**Pass criterion:** B creates a repeatable, *audibly better* original
response than A and C on the same input; merely mentioning "Illmatic"
or outputting valid JSON does not count.

## Deployment boundary

All web research and metadata collection may be conducted OFFLINE
from the stage beforehand; the show itself may have no internet.
Only local preapproved text cards and local model inference are loaded
during rehearsal. For the Oct 29, 2026 show, the current reliable Logic
performance continues even if Qwen times out. No automatic live routing
until actual 8 GB Mac measurements and artist acceptance.
