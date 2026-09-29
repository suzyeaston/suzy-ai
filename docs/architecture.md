# Architecture

## One brain, multiple organs

SUZY//AI is a local control plane.

It does not replace the applications.

```text
                  ┌──────────────────────┐
                  │       SUZY//AI       │
                  │                      │
                  │ model adapters       │
                  │ private memory       │
                  │ tool broker          │
                  │ timeline/event bus   │
                  │ provenance           │
                  └──────────┬───────────┘
                             │
              local protocol│
                 ┌───────────┴───────────┐
                 │                       │
        ┌────────▼────────┐     ┌────────▼────────┐
        │   APPLIANCE     │     │  POP//CONTEXT  │
        │                 │     │                │
        │ musical actor   │     │ observer       │
        │ visual actor    │     │ interpreter    │
        │ timeline UI     │     │ evidence       │
        └────────┬────────┘     └─────────────────┘
                 │
        ┌────────▼────────┐
        │ TOASTER / BLE   │
        │ control surface │
        └─────────────────┘
```

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
