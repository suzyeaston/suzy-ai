# SUZY//AI

**Local intelligence for music, cultural context, and creative instruments.**

SUZY//AI is an open-source project by [Suzy Easton](https://www.suzyeaston.ca/),
developed as a local system for musical perception, memory, interpretation, and
creative interaction. This repository implements its shared memory and inference
core. **POP//CONTEXT is its audiovisual input pipeline**, maintained in a separate
repository. Together they contribute to the same music-AI direction.

The aim is to build musical AI whose responses can be informed by a developing
body of taste: album reviews, musical ideas, listening observations, cultural
references, humour, and connections between them. Threads contributed by Suzy are
part of that material. Each adds examples of language, association, or musical
judgement that can remain available beyond a single conversation.

The longer-term goal is for those references to inform creative decisions in
**The Appliance Latent Space** and related music tools: suggestions about phrasing,
texture, arrangement, and audiovisual behaviour that a musician can audition,
accept, or change. That connection is being developed. The current core supports
local text conversation and memory retrieval; it does not yet listen to audio or
control the instrument.

## How the projects fit together

Repository boundaries organize the code. SUZY//AI is the overall intelligence
system; its core and POP//CONTEXT input pipeline have complementary responsibilities.
The Appliance is the instrument, with SUZY//WORLD and the website providing
selected public knowledge and interfaces.

| Project | Existing role | Connection to the music-AI direction |
|---|---|---|
| **[SUZY//AI](https://github.com/suzyeaston/suzy-ai)** | Local text inference, private memory, teaching APIs, events and timelines | Provides the core in which contributed examples can be retained and recalled; musical decision-making is a development goal |
| **[The Appliance Latent Space](https://github.com/suzyeaston/appliance-latent-space-live)** | Playable browser instrument with patterns, synthesis, arrangements, scenes and synchronized visuals | Intended to receive musically relevant suggestions through its control/event language, while remaining playable without AI |
| **[POP//CONTEXT](https://github.com/suzyeaston/pop-context)** | SUZY//AI audiovisual input pipeline: media windows, transcripts, representative frames and timestamps | Intended to supply approved observations with evidence and timing; cultural AI interpretation remains future work |
| **[SUZY//WORLD](https://github.com/suzyeaston/suzy-world)** | WordPress plugin and public API for versioned album reviews, entities, tags and relationships | Holds deliberately published cultural knowledge that could support public music interfaces |
| **[suzyeaston.ca](https://github.com/suzyeaston/suzyeastonca)** | Public website and creative lab, including Loop Lab, Track Analyzer and other music experiments | A future surface for selected SUZY//AI capabilities and outputs; the website does not currently access private memory |

POP//CONTEXT prepares evidence for the same memory and interpretation system that
uses contributed threads, album reviews, and musical examples. It does not need a
separate musical identity or cultural-memory database. Its approved-evidence
transfer into the core is planned; the complete pipeline is not operational yet.
The published integration notes describe the intended connections. The [app registry](config/apps.json),
[Appliance integration notes](https://github.com/suzyeaston/appliance-latent-space-live/blob/main/docs/suzy-ai-integration.md)
and [POP//CONTEXT integration notes](https://github.com/suzyeaston/pop-context/blob/main/docs/suzy-ai-integration.md)
record those contracts.

The Appliance already includes local example-based mapping between musical and
visual controls. Its seeded musical variations are separate from the language
model here. A future AI sound/proposal layer will need its own implementation and
listening tests.

## Building taste through examples

The collection can grow through ordinary material supplied over time:

- album reviews and discussions of production, performance, or arrangement;
- musical phrases, voicings, textures, and explanations of particular choices;
- threads containing a question or setup and several replies;
- wordplay, references, and cultural associations;
- later corrections or comparisons that refine an earlier interpretation.

Humour belongs in this collection because musical references also carry language,
context, and association. A band-name thread can demonstrate those relationships;
it is one kind of example within the broader musical project.

The first public thread asks **“What do you think about Mormon music?”** Its replies
include “The Joseph Smiths” and “The Mormonissey years.” The
[full example](docs/build-in-public/2026-10-08-humour-memory.md) preserves all six
replies, with [the approved input available as JSON](examples/threads/mormon-music.json).
Suzy supplied and selected the material; individual reply authors are unspecified.
Selection records an example of interest, not authorship of every reply or agreement
with every statement.

The current workflow saves the whole thread as one approved memory. Further
contributed threads can extend the collection without replacing earlier examples.
Original wording, context, and available attribution stay with the material.
Individual reply relationships and automatic categorization remain future work.

## What learning means at this stage

The current model is Qwen3 1.7B, running locally through llama.cpp. Saved notes are
retrieved into its conversational context. Topic matches and a small background
selection of notes labelled as humour, taste, preferences, or style support recall
without requiring the original topic phrase every time.

This provides continuity and examples for a response; it does not change model
weights or establish a learned musical style. The next steps are to evaluate how
well the examples inform conversation, improve retrieval and musical representation,
and connect approved suggestions to the instrument. Fine-tuning is a later option
once suitable examples and evaluation criteria exist.

## Working now: v0.3

| Capability | Current behaviour |
|---|---|
| Local conversation | A model running on your computer, with no required commercial API |
| Mac setup | Verified model download and a launcher for the model plus SUZY//AI |
| Saved memory | Explicitly approved notes in private SQLite storage |
| Recall | On by default; bounded topic matches plus labelled humour/taste examples |
| Threads | A whole setup-and-replies exchange stored as one document |
| Provenance | Source labels, timestamps, and the actual retrieved excerpts |
| Teaching surfaces | Albums, musical ideas, idioms, and world notes in the existing world store |
| Shared infrastructure | JSON event protocol, timeline, app registry, and local HTTP API |

There is no weight training, automatic thread classification, autonomous tool
execution, or automatic chat-history saving. Recall can miss relevant material,
and a small model can still make mistakes or make an unsuitable musical or cultural association.

## Run on an Apple Silicon Mac

From a fresh clone:

```bash
git clone https://github.com/suzyeaston/suzy-ai.git
cd suzy-ai
bash scripts/setup-mac.sh
bash scripts/start-mac.sh
```

Setup installs the tools, runs tests, and downloads the model once. Later launches
reuse the verified file. See [Mac setup](docs/mac-setup.md) for requirements and
troubleshooting.

If ports are already in use:

```bash
bash scripts/start-mac.sh --api-port 7332 --model-port 8082
```

Wait for `Local inference test passed` and the `you >` prompt. Then chat normally.
Saved-memory recall starts on; `/memory off` pauses it for the session.

**`you >` is a chat prompt. Your Terminal shell prompt usually ends in `%` or `$`.**
To run an update command, first exit chat with `/quit` or Ctrl-C. New versions also
accept plain `quit` and `exit`, and recognize common accidentally pasted setup
commands without forwarding them to the model. No chat command executes a shell.

### Updating an existing checkout

After leaving chat, update the branch you are using:

```bash
git pull --ff-only
bash scripts/start-mac.sh --api-port 7332 --model-port 8082
```

An update from GitHub cannot affect a process that is already running: restart to
load the new code. There is no need to rerun setup or download the model just to
pick up a code change. If testing a PR branch, use that PR's checkout instructions.

### Core only / other local model servers

Python 3.11+ is required. Install with `pip install -e .` in a virtual environment,
then use `suzy-ai init`, `suzy-ai doctor`, and `suzy-ai serve`. The core defaults to
`http://127.0.0.1:7331`; inference requires a configured local model server.

See the [chat and memory API guide](docs/local-chat.md) for approved memory writes,
search, deletion, model configuration, and the local-process trust boundary.

## Public development and local memory

The public repository contains code, selected examples, and build notes. Local
memory, recordings, model weights, and world timelines live outside the checkout:

```text
~/.suzy-ai/
```

Publishing a selected thread creates a public copy of that example; it does not
sync the private database. A fresh clone does not automatically ingest the public
examples into memory. Existing world teachings also require deliberate inclusion
in the retrieval store. Local chat history remains in process and is not saved.

## Building in public

- [Threads as musical and cultural memory](docs/build-in-public/2026-10-08-humour-memory.md)
- [The approved thread input as JSON](examples/threads/mormon-music.json)
- [Architecture](docs/architecture.md) and [roadmap](docs/roadmap.md)

The public collection will grow as Suzy contributes more threads and musical
examples. GitHub records the selected material and the development around it:
what was supplied, what was saved, and what was actually evaluated. Build notes
separate contributed examples from generated responses and verified results from
plans. Publishing remains separate from local memory capture.

## Development priorities

1. Make continued thread capture and retrieval easier while preserving context.
2. Represent musical preferences and associations in ways that can be evaluated.
3. Connect the core to the Appliance's musical controls and proposal workflow.
4. Introduce approved audiovisual observations from POP//CONTEXT.
5. Expose selected cultural knowledge and creative outputs through SUZY//WORLD
   and the website's music interfaces.

The laptop remains the compute/audio host. Physical controls can later send
logical events to the instrument. The instrument should retain reliable playback,
explicit audition/accept, and an immediate Kill independently of AI availability.
`scripts/sync-apps.sh` manages sibling application checkouts.

## Development

```bash
bash scripts/test.sh
```

Tests use temporary private state and synthetic model services. CI includes Linux
and macOS. Passing those tests establishes software behaviour, not musical judgement.
Listening sessions and conversational evaluations will assess the creative results.

See [world-model storage](docs/world-model.md), [teaching surfaces](docs/teaching-surfaces.md),
and [timeline/event architecture](docs/architecture.md) for the existing systems.

Code is licensed under Apache-2.0. Attribution for shared thread examples is recorded
with the examples; do not assume every supplied reply was authored by Suzy or by AI.
