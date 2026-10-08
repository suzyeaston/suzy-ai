# POP//CONTEXT: SUZY//AI audiovisual input pipeline

POP//CONTEXT is the audiovisual input component of SUZY//AI, maintained in the
[pop-context repository](https://github.com/suzyeaston/pop-context). Separate
repositories allow the media tools and inference core to develop independently.

## Responsibilities

POP//CONTEXT owns local media ingest, transcripts, representative frames,
timestamped evidence and the local evidence report. Richer audio and visual
perception remain development goals.

The SUZY//AI core owns shared inference, private memory, world teachings,
provenance and event storage. Cultural interpretation and musical taste develop
within this shared system, alongside contributed threads, album reviews and
musical ideas. POP//CONTEXT should not introduce a second cultural-memory database.
Research tools remain future work.

## Current boundary and intended connection

The evidence pipeline runs locally and produces files. It does not automatically
send evidence into SUZY//AI, save it as conversational memory, or publish it.
The core currently accepts text; it does not consume raw audio or video.

An approved-transfer workflow should retain source media identifiers, timestamps,
exact excerpts and the distinction between observation and model interpretation.
The existing `/v1/teach` API stores world teachings; `/v1/memory` stores explicitly
approved retrieval notes. A world teaching is not automatically chat-retrievable.
See [local chat and memory](local-chat.md) and [teaching surfaces](teaching-surfaces.md).

The eventual connection should make relevant evidence available to the same
memory and interpretation layer that uses Suzy's contributed examples. It should
preserve uncertainty and attribution, keep media local by default, and require a
separate deliberate step for public publication.
