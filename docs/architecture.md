# Architecture

## One system, specialized components

SUZY//AI is the overall local intelligence system for musical perception, memory,
interpretation, and creative interaction. This repository implements the core;
POP//CONTEXT is its audiovisual input pipeline in a separate repository.

| Component | Responsibility | Status |
|---|---|---|
| SUZY//AI core | Local text inference, approved memory retrieval, world teachings and events | Implemented; retrieval memory and world teachings remain separate stores |
| POP//CONTEXT input pipeline | Media ingest, transcripts, frames and timestamped evidence | Local evidence pipeline works; automatic transfer to the core is not implemented |
| Appliance instrument | Musical and visual interaction | Playable independently; AI proposals and control integration are future work |
| SUZY//WORLD and website | Deliberately published knowledge and public interfaces | Separate applications; no automatic private-memory access |

Cultural interpretation and developing musical taste belong to the shared
SUZY//AI direction. POP//CONTEXT supplies evidence for that work rather than
maintaining a second cultural-memory system. Threads, album reviews, and approved
media observations can eventually inform the same conversational and musical
context. This is an integration goal, not a claim that the stores or applications
are already connected. See [the input-pipeline contract](pop-context.md).

## The toaster decision

The toaster does not need to contain the AI.

A cleaner physical architecture is:

```text
toaster sensors / knobs / plunge
            ↓ Bluetooth
logical control events
            ↓
computer
            ↓
Appliance + SUZY//AI + audio + visuals
```

This matches the existing Appliance principle:

> a control is a logical name, not a knob.

The physical object becomes an expressive controller. The computer remains the power/compute/audio host.

## Local AI

SUZY//AI should not hard-code a single model vendor.

Future adapters may target:

- llama.cpp,
- MLX,
- Ollama,
- other open-weight runtimes,
- optional remote providers when explicitly enabled.

Applications ask SUZY//AI for a capability, not a brand name.

## Memory

Private state lives under `~/.suzy-ai`.

The public repository is machinery, not identity.

Potential private material:

- memory,
- corrections,
- recordings,
- cultural notes,
- research cache,
- training data,
- local model weights,
- world timeline.

## Research

A local model can remain local and still request current information.

The future tool broker should make freshness explicit:

```text
question
   ↓
does this depend on the current world?
   ↓ yes
research request
   ↓
sources + timestamps + provenance
   ↓
local reasoning
```

External research is an instrument, not the mind.

## Timeline

Timeline is a core primitive with multiple coordinate systems.

| Stream | Coordinate | Example |
|---|---|---|
| music | bar / beat | Appliance arrangement |
| media | seconds | POP//CONTEXT evidence |
| world | ISO 8601 | lived/research/project events |

Applications keep their specialized UIs.

SUZY//AI only defines the event grammar that lets those timelines talk to each other.

## Implemented in v0.3

`server.py` validates local HTTP requests, `chat.py` composes bounded context,
`memory.py` retrieves explicitly approved notes from private SQLite FTS5, and
`inference.py` sends text-only requests to a configured loopback model server.
The adapter protocol is replaceable. There is no tool execution or cloud fallback.
World teachings and timelines keep their existing formats. See
[local chat](local-chat.md) for configuration, API contracts, and trust boundaries.
