# SUZY//AI

**A local AI experiment in musical taste, humour, and memory — built in public.**

By [Suzy Easton](https://www.suzyeaston.ca/). A place for album reviews, strange
connections, music questions, and threads that make me laugh. Save the examples,
keep their context, and see what a local model can do with them in conversation.

One of the first public examples starts here:

> **What do you think about Mormon music?**
>
> I'm partial to the The Joseph Smiths... The Mormonissey years, at least.

The [full thread](docs/build-in-public/2026-10-08-humour-memory.md) has six replies.
Suzy supplied and selected the examples; individual reply authors are unspecified.

This is a working project, with the experiments and limitations visible alongside
the code. The model is currently Qwen3 1.7B running through llama.cpp on a local Mac.
Saving examples gives it material to retrieve; it does not retrain its weights.

## The direction

Start with a thread: a setup or question, followed by the replies worth keeping.
Preserve the wording and any known attribution. Let humour, musical taste, and
unexpected associations coexist in the same collection.

The current workflow saves a thread as one approved memory through the local API.
Chat recalls saved notes automatically. A small background selection of notes
labelled as humour, taste, preferences, or style helps bring examples into
conversation without requiring the original topic phrase every time. These are
lexical rules; automatic categorization and a dedicated thread-entry interface
are still to come.

Threads Suzy contributes for the public collection will become examples and build
notes here on GitHub. The repository documents what was supplied, what was saved,
and what was actually tested. Generated riffs can become selected public drafts
later; generated text is not automatically a new memory or a published post.

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
and a small model can still make mistakes or write an unfunny joke.

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

## Open machinery. Personally owned intelligence.

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

- [Teaching SUZY//AI what makes me laugh](docs/build-in-public/2026-10-08-humour-memory.md)
- [The approved thread input as JSON](examples/threads/mormon-music.json)
- [Architecture](docs/architecture.md) and [roadmap](docs/roadmap.md)

More contributed threads and music examples will extend this collection. A public
example can be funny, exploratory, unfinished, or something that did not work;
notes should distinguish supplied material from generated output and verified
results from plans.

## Later: the website and music app

The longer-term direction is to connect this memory and conversational system to
Suzy's website and **The Appliance Latent Space** music app: musical prompts,
creative interactions, and selected public outputs. That integration is future
work. The music app is not currently driven by this chat launcher, and the website
has no access to the private memory store.

The related applications remain separate repositories:

- [Appliance Latent Space](https://github.com/suzyeaston/appliance-latent-space-live)
  — the musical and visual instrument, with physical controls as a future input.
- [POP//CONTEXT](https://github.com/suzyeaston/pop-context) — media interpretation.
- [Website](https://github.com/suzyeaston/suzyeastonca).
- [SUZY//WORLD](https://github.com/suzyeaston/suzy-world) — deliberately published
  cultural knowledge; see the [public/private boundary](docs/public-world.md).

The shared event/timeline protocol and [app registry](config/apps.json) provide a
base for those connections. `scripts/sync-apps.sh` manages sibling app checkouts.

## Development

```bash
bash scripts/test.sh
```

Tests use temporary private state and synthetic model services. CI includes Linux
and macOS. Passing those tests does not establish the quality of model-generated
jokes; real listening and conversational experiments are part of the work.

See [world-model storage](docs/world-model.md), [teaching surfaces](docs/teaching-surfaces.md),
and [timeline/event architecture](docs/architecture.md) for the existing systems.

Code is licensed under Apache-2.0. Attribution for shared thread examples is recorded
with the examples; do not assume every supplied reply was authored by Suzy or by AI.
