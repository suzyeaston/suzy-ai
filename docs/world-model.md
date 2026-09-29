# Living world model

SUZY//AI is not a static preference profile.

It keeps canonical **entities** and historical **teachings**.

```text
Björk — Homogenic
      │
      ├── review, 2026
      ├── revised review, 2027
      └── new connection, 2029
```

The album remains one entity. The person's development remains visible.

## Deduplication

Every entity has a normalized key. Every teaching has a content fingerprint.

Exact repeated submissions create neither another teaching nor another timeline event.

Changed content becomes a new teaching attached to the same entity.

## Private storage

```text
~/.suzy-ai/world/world.sqlite3
~/.suzy-ai/world/timeline.jsonl
```

Neither belongs in Git.

## Teaching API

```text
POST /v1/teach
POST /v1/teach/album
POST /v1/teach/music
POST /v1/teach/idiom
POST /v1/teach/world-note
```

Read:

```text
GET /v1/world/stats
GET /v1/world/entities
GET /v1/world/entities?kind=album
GET /v1/world/teachings
GET /v1/world/teachings?domain=music
```

The future reasoning model will retrieve relevant slices of this world. It must not silently rewrite human teachings. Inferred connections need their own provenance.
