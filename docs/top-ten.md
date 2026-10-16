# Thread-to-Top-Ten parody drafts

SUZY//AI's comedy direction is original parodies inspired by David Letterman's
Top Ten list format: a dry setup, concise musical wordplay, escalating surprises,
and a closing joke at number one. These are new SUZY//AI drafts, not transcripts
of the show. Audio/video performance and voice delivery are not implemented here.

## Source and draft are separate

- `examples/threads/` keeps the original setup and replies in the existing approved
  memory-import format. This update does not change those files or private memories.
- `examples/top-ten/` contains two curated countdown drafts. The Mormon-music source
  has six replies, so its ten-entry adaptation includes new material. The longer
  bathroom-music thread is selected and rewritten into ten entries.
- A countdown has a title, one setup and exactly ten entries ordered 10 through 1.
  Each entry has `rank`, `text` and `source_items`: the original reply numbers used,
  or an empty array for a new joke. References indicate inspiration, not quotation.
- Nested replies remain attached to their parent when preparing model input.
  Original reply order is not a comedic ranking; the draft supplies a new order.

## Render a curated list without a model

From the repository root (Python 3.11+):

```bash
python3 -m suzy_ai.cli top-ten \
  --thread examples/threads/mormon-music.json \
  --list examples/top-ten/mormon-music.json
```

Use the `best-music-to-take-a-crap-to.json` filenames for the second list. Add
`--format json` to inspect source references and draft metadata. Curated rendering
is deterministic and does not make an inference request.

## Generate a new local-model draft

Use an already-running local model server and the existing inference environment
settings described in [the chat guide](local-chat.md). For example, with your model
server listening on port 8082, set `SUZY_AI_INFERENCE_URL=http://127.0.0.1:8082/v1`
and `SUZY_AI_MODEL` to the model name/alias that server exposes. The CLI does not
automatically inherit settings from another running process or load `.env`.

```bash
python3 -m suzy_ai.cli top-ten \
  --thread examples/threads/mormon-music.json \
  --generate --format json
```

This calls the existing local-only inference adapter directly. It does not call
the core's chat endpoint or share its single-request semaphore. Run comedy drafting
outside the live performance session to avoid competing with musical inference.
No model downloads, personal-memory retrieval, file writes or publishing happen.
Output goes to stdout and remains a draft until reviewed. Generation is capped at
2048 output tokens and validated as JSON; malformed/incomplete lists fail explicitly
rather than being silently padded or labelled approved. Model availability and
actual joke quality still need evaluation with the local Qwen setup.

The validator rejects missing/extra entries, incorrect countdown order, duplicate
punchlines, overlong lines and references to nonexistent source replies. Model
source references still need editorial review: schema validation cannot establish
whether a joke actually draws on the cited reply.

## Review and future performance

Edit the setup, choose the strongest closer, and read the list aloud. The source
archive remains intact while individual parody drafts can evolve. Future work can
add timing, host introductions and audiovisual delivery on top of this structured
countdown; none of it needs to run inside the musical looper's audio path.
