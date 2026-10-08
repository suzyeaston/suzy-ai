# SUZY//AI v0.3: private retrieval and local chat

The existing Python HTTP service, world teachings, timeline and local teaching UI
remain in place. New `inference.py`, `memory.py` and `chat.py` modules add an adapter
contract, an explicitly approved private document store, and stateless chat. No
Python dependencies or model downloads are added.

## Start

Install the core as described in the README. Start your own local, OpenAI-compatible
model server with a model already installed. Select its exact model name:

```bash
export SUZY_AI_MODEL='your-installed-local-model'
export SUZY_AI_INFERENCE_URL='http://127.0.0.1:11434/v1'
export SUZY_AI_INFERENCE_TIMEOUT=60
suzy-ai serve
```

Ollama's local compatibility endpoint is `/v1/chat/completions`; a locally configured
llama.cpp server can use the same contract (often port 8080). See the official
[Ollama compatibility documentation](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx)
and [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
The adapter sends model, messages, `stream: false` and `max_tokens`; it accepts a
non-empty assistant text response. Tool/function-call responses are rejected.

An unset `SUZY_AI_MODEL` disables inference. `.env.example` documents settings but
is not automatically loaded. A configured endpoint is **not** proof of local
compute: use a trusted runtime with cloud models, forwarding and telemetry disabled.
SUZY//AI cannot control networking or logging performed by a separately run server.
For a stronger boundary, run the model runtime without outbound network access.

## Store an approved note

```bash
curl --fail-with-body http://127.0.0.1:7331/v1/memory \
  -H 'Content-Type: application/json' \
  -d '{"title":"Synth experiment","text":"The cedar resonator sounded warm with a slow attack.","source":"manual:studio-notes","approved":true}'
```

Returns the note's `id`, title, text, source and creation time (201).
`approved` must be the literal boolean `true`; the caller is explicitly choosing to
save the submitted text. This flag is an intent check, not a separate authorization
system. Title: 200 characters; text: 20,000; source: 500. Notes are immutable; to
correct a note, explicitly delete it by ID and add the corrected text with provenance.

Data lives in `~/.suzy-ai/memory/memory.sqlite3`, or under `SUZY_AI_HOME`.
The directory/file have POSIX modes 0700/0600. This is not encryption at rest.
A source checkout rejects `SUZY_AI_HOME` inside that checkout. Do not put private
state inside another public repository. No memory text is appended to the timeline.

Existing `world/world.sqlite3` teachings are preserved and are **not automatically
copied into retrieval**. To include a teaching, deliberately submit its chosen text
to `/v1/memory` with its teaching ID in `source`. This keeps ingestion explicit and
avoids silently ingesting all historical or personal records. `source` is a label,
never a file path to open or a URL to fetch. No filesystem scanning occurs.

## Search or delete

```bash
curl --fail-with-body http://127.0.0.1:7331/v1/memory/search \
  -H 'Content-Type: application/json' -d '{"query":"cedar resonator","limit":5}'

# Replace the placeholder with the actual returned note ID.
curl --fail-with-body http://127.0.0.1:7331/v1/memory/delete \
  -H 'Content-Type: application/json' -d '{"id":"mem_REPLACE_WITH_NOTE_ID"}'
```

Search returns `sources` with IDs, titles, source labels, timestamps and excerpts.
SQLite FTS5 ranks lexical matches using BM25. Queries are tokenized and quoted;
caller input cannot become SQL or FTS operators. At most 32 unique query tokens,
10 results and 6,000 serialized source characters enter chat. This is lexical
retrieval, **not embeddings**, and can miss paraphrases. Python's SQLite must include
FTS5 (the tests verify it). Search creates an empty store if none exists.

Deletion removes the note and rebuilds the search index. Unknown IDs return 404.
Deletion is not a forensic erase guarantee and cannot erase copies in backups or
in an external model runtime's logs. With the service stopped, back up the private
home to a private destination; never commit it to the public source repository.

## Chat

```bash
curl --fail-with-body http://127.0.0.1:7331/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What did I note about the cedar resonator?","use_memory":true,"memory_limit":5,"max_tokens":512}'
```

Response includes `id`, `created_at`, `model`, an assistant `message`, `sources`,
`memory_used` and `stored: false`. Sources identify the actual retrieved excerpts;
they do not certify the answer as accurate. Inline model-generated citations can
still be wrong. `memory_used` means sources were supplied, not that the model relied
on them. `use_memory` defaults to false. No chat turns, prompts or answers are saved.

Optional `history` accepts at most 12 `{role, content}` objects, restricted to user
and assistant roles. Each turn/message is limited to 8,000 characters; history to
16,000 combined characters. `max_tokens` is an integer from 1 to 2,048. The caller
owns conversational state. Unknown fields (including endpoint/model overrides and
tool requests) are rejected. This is SUZY//AI's API, not an OpenAI API replacement.

## Boundaries and errors

- The service binds only to loopback, including when `serve()` is called directly.
- Every route validates Host and Origin, rejects cross-site browser requests, and
  removes the old wildcard CORS policy. The existing same-origin teaching UI works.
  Apps on other browser origins must use their own trusted local backend; there is
  no cross-origin allowlist in this release. Local command-line clients need no Origin.
- POSTs require JSON and one valid Content-Length, at most 128 KiB. HTTP reads have
  a 15-second socket idle timeout. Request URLs/bodies and answers are not logged.
- Inference URLs accept HTTP loopback IP literals or `localhost` (pinned to
  127.0.0.1), with path `/v1`. No DNS for arbitrary hosts, proxies, URL credentials,
  redirects, remote fallback, runtime launch, or model download occurs.
- The inference deadline defaults to 60 seconds, configurable up to 120; output is
  capped at 256 KiB and only one model request runs at a time. Model server errors
  never expose backend response bodies or exception details.
- Chat separates reference data from the system prompt. Prompt instructions are
  defense in depth, not a guarantee against prompt injection. There are no tools,
  command execution, automatic learning or autonomous actions to invoke.
- This is a single-user local service, not an authenticated multi-user server.
  Trusted local programs can access its APIs. Loopback does not protect against
  compromised software or another user/process on the same machine.

HTTP statuses: 400 invalid input; 403 disallowed host/origin; 404 unknown route or
note; 429 inference busy; 502 invalid model response; 503 disabled/unavailable model
or storage; 504 inference deadline. `/health` reports core health/version, not model
readiness. v0.3 provides no consciousness or sentience claim.

## Verification

```bash
bash scripts/test.sh
```

Tests use only synthetic data, temporary private homes and loopback fake model
servers. They cover local-only transport, proxy/redirect rejection, deadlines,
response bounds, memory approval/retrieval/deletion/provenance, chat validation and
non-persistence, browser access controls, and the existing teaching/timeline flows.
A real installed model still needs a smoke test on the user's machine.
