# SUZY//AI

**A local-first, open-source intelligence core for creative machines, cultural interpretation, and personal world-building.**

SUZY//AI is the shared nervous system beneath a family of experiments by [Suzy Easton](https://www.suzyeaston.ca/).

It is deliberately **not one giant app**.

```text
                         SUZY//AI
                  local brain + memory
                   protocol + timeline
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
  APPLIANCE LATENT SPACE            POP//CONTEXT
     create / perform              observe / interpret
     music / visuals               video / audio / culture
     physical controls             research / evidence
```

The laptop/computer is the compute host.

The physical toaster can become a Bluetooth control surface that emits the same logical controls as keyboard, MIDI, or browser UI. It does not need to run the AI itself.

## Why a separate core?

The Appliance and POP//CONTEXT were independently converging on the same requirements:

- local inference,
- private user data,
- inspectable events,
- personal learning,
- replaceable models,
- timeline-based interaction,
- optional access to the current world.

SUZY//AI owns those shared contracts without swallowing the applications.

## The rule

> **Open machinery. Personally owned intelligence.**

The source code can be cloned by anyone.

Your private memory, recordings, model files, training examples, research cache, and world timeline live outside the repository under:

```text
~/.suzy-ai/
```

A fresh clone starts with an empty identity.

## Current v0.3

SUZY//AI currently provides:

- a language-neutral JSON event protocol,
- a shared timeline event format,
- an application registry,
- a local state directory,
- a localhost HTTP event/timeline and teaching server,
- a local-only inference adapter and stateless chat API,
- explicitly approved private notes with source-aware lexical retrieval,
- a CLI for initializing, inspecting, and writing timeline events,
- no required cloud account,
- no required commercial model API.

It does **not** claim to contain a trained Suzy model yet.

## Install

Python 3.11+.

```bash
git clone https://github.com/suzyeaston/suzy-ai.git
cd suzy-ai

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

suzy-ai init
suzy-ai doctor
```

Run the local core:

```bash
suzy-ai serve
```

Default:

```text
http://127.0.0.1:7331
```

Health check:

```bash
curl http://127.0.0.1:7331/health
```

The server binds to loopback only by default.

## Timeline

The timeline is a shared primitive, not a single musical UI.

The Appliance can render **musical** events by bars/beats.

POP//CONTEXT can render **media** events in seconds.

SUZY//AI can store **world** events in real time.

Example:

```bash
suzy-ai timeline add \
  --stream world \
  --kind note \
  --text "First SUZY//AI event."
```

Then:

```bash
suzy-ai timeline list --stream world
```

## Existing apps

See [`config/apps.json`](config/apps.json).

The apps remain independent repositories:

- `suzyeaston/appliance-latent-space-live`
- `suzyeaston/pop-context`
- `suzyeaston/suzyeastonca`

Use:

```bash
./scripts/sync-apps.sh
```

to clone/update local sibling copies in `~/Projects/suzy-ai-workspace/apps`.

## Open source

Licensed under Apache-2.0.

Open source does not prevent a future business. Possible paid layers can include hosted inference, hardware, curated model/data packs, collaboration, managed sync, installation, support, performances, and specialized interfaces while the core remains open.

## Local chat and private memory

On an Apple Silicon Mac, start with [Mac setup](docs/mac-setup.md):

```bash
bash scripts/setup-mac.sh
bash scripts/start-mac.sh
```

See [the v0.3 setup and API guide](docs/local-chat.md) for model configuration,
approved memory writes, retrieval, deletion, chat, and privacy boundaries.
Inference stays disabled until a local model is configured; chat does not save
conversations or use memory unless requested.

## Next

1. adapters from Appliance and POP//CONTEXT into the local event server,
2. machine-aware local model selection,
3. semantic retrieval and approved corrections,
4. private export/backup tooling,
5. explicit web research tool with provenance,
6. audio/vision perception services,
7. learning from approved corrections and examples.

See [`docs/architecture.md`](docs/architecture.md) and [`docs/roadmap.md`](docs/roadmap.md).


<!-- WORLD-MODEL-V02 -->

## Teach SUZY//AI

SUZY//AI 0.2 adds a private living world model and a local teaching interface:

```text
http://127.0.0.1:7331/
```

Current teaching surfaces:

- album reviews,
- musical ideas / chords / influences,
- idioms and expressions,
- generic world notes, including Canucks and culture.

Everything writes through one deduplicating API into:

```text
~/.suzy-ai/world/world.sqlite3
```

Exact repeat submissions are ignored. Changed interpretations become new historical teachings attached to the same entity.

This lets the system preserve **character development** instead of rewriting the past.

See:

- [`docs/world-model.md`](docs/world-model.md)
- [`docs/teaching-surfaces.md`](docs/teaching-surfaces.md)
- [`docs/wordpress-page.md`](docs/wordpress-page.md)


<!-- SUZY-WORLD-PUBLIC -->

## Public knowledge: SUZY//WORLD

Private intelligence and public knowledge are separate systems.

- **SUZY//AI** owns private memory, learning, timelines, models, and inference.
- **SUZY//WORLD** holds only deliberately published entities, reviews, tags, relationships, and media metadata.

Public API:

```text
https://www.suzyeaston.ca/wp-json/suzy-world/v1
```

Source:

```text
https://github.com/suzyeaston/suzy-world
```

See [`docs/public-world.md`](docs/public-world.md).
