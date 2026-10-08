# Mac setup: a small local SUZY//AI

Designed for an Apple Silicon Mac, initially an M2 with 8 GB unified memory.
This uses llama.cpp with Qwen3 1.7B Q4_K_M. It is a small general-purpose model,
not a model trained on Suzy's life or sounds. Performance and answer quality must
be checked on the actual Mac; CI uses synthetic data and fake services.

## First run

From your checkout:

```bash
bash scripts/setup-mac.sh
bash scripts/start-mac.sh
```

Setup installs Homebrew if absent, then Python 3.12 and llama.cpp, creates a
separate `.venv-mac`, installs this checkout, runs tests and downloads the model.
Homebrew's official installer may request your Mac login password and Command Line
Tools. Keep Terminal open and follow its prompts. Setup needs internet; allow
several GB of free storage. The model alone is approximately 1.28 GB. No cloud AI
account, API subscription, or Ollama installation is needed.

The model comes from the
[llama.cpp maintainers' Qwen3 repository](https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF).
The Apache-2.0 model is pinned to revision
`daeb8e2d528a760970442092f6bf1e55c3b659eb`; its
[published SHA-256](https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/blob/daeb8e2d528a760970442092f6bf1e55c3b659eb/Qwen3-1.7B-Q4_K_M.gguf)
is checked before installation and on launch. Interrupted downloads resume; a bad
checksum stops setup. Dependencies installed via Homebrew use its available
formula version rather than a pinned runtime build. See the official
[formula](https://formulae.brew.sh/formula/llama.cpp) and
[server options](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

Setup preserves any existing `.venv`, private memories and world teachings. The
model is stored at `~/.suzy-ai/models/Qwen3-1.7B-Q4_K_M.gguf` (or `SUZY_AI_HOME`).
It is never committed. If an existing model fails verification, move it aside;
setup will not overwrite it. A failed partial download can be removed and retried.

## Use

```bash
bash scripts/start-mac.sh
```

The launcher verifies the file, loads the model, starts SUZY//AI, and sends a
synthetic hello to test the full chat path. Then type at `you >`.

- `/memory on` includes matching previously approved notes in subsequent requests.
- `/memory off` disables retrieval (the default).
- `/reset` clears in-process chat history.
- `/quit`, Ctrl-D, or Ctrl-C stops the two child services started by this launcher.

Chat history is not saved. The terminal retains at most two prior exchanges with
a combined 4,000-character limit. Messages are capped at 2,000 characters. It does
not automatically create memories; use the explicit approval API in
[local-chat.md](local-chat.md). Terminal scrollback may still contain displayed text.

The core API is `http://127.0.0.1:7331`. Model inference runs on port 8081 with a
random per-launch API key passed privately between the processes, not printed or
written to disk. The model's standalone web UI is disabled. The existing teaching
UI remains at the core's root URL; it is not a chat screen.

For API-only use:

```bash
bash scripts/start-mac.sh --no-chat
# Or choose alternate ports if an existing service occupies the defaults:
bash scripts/start-mac.sh --api-port 7332 --model-port 8082
```

## Resource and privacy boundaries

The launcher uses a 4,096-token context, one inference slot, four CPU threads,
Metal GPU offload, smaller batches, and disabled extended thinking. It requests
at most 384 output tokens for terminal chat. Close heavy applications for the
first test, and measure again before using it alongside live audio. Large or
non-English prompts can still exceed the token context despite character caps;
shorten the message or `/reset` if the model rejects a request.

Only explicit setup downloads software and weights. Ordinary launch passes the
local model file and `--offline` to llama.cpp and never downloads a model. It
removes inherited `LLAMA_*` settings, disables model logging, and adds no tool,
agent or filesystem-execution capabilities. This is an application configuration,
not an OS network sandbox. No process is installed as a background login service.
The existing single-user local-process trust boundary still applies.

If a port is busy, the launcher stops without killing or adopting an existing
process. Stop an earlier `suzy-ai serve` yourself or select different ports. If
llama.cpp exits during startup, check `llama-server --version`, available memory,
and that the installed runtime supports the documented flags. Update llama.cpp
with Homebrew if required. Startup logs are not persisted.

## Tests

`bash scripts/test.sh` includes checksum/install/reuse tests, port collision checks,
owned-process cleanup, inherited runtime setting isolation, terminal memory
opt-in/reset, and authenticated loopback inference. These tests do not download
weights or install Homebrew. The shell scripts also have a `bash -n` check in CI.

## First Mac setup regression (fixed)

The first on-device setup installed Homebrew, Python, llama.cpp and SUZY//AI, then
stopped at the test gate with two socket-related errors. The real model download
had not started; earlier model messages came from synthetic fixtures.

- A bound, non-listening socket can time out on macOS. The refusal-classification
  test now injects a refusal deterministically; real timeout tests remain.
- Closing a rejected oversized request with unread input could reset the client
  connection. Responses now have explicit byte lengths, and early rejections
  close the write side then drain at most 256 KiB/100 ms of unread socket input.
- Fixture progress output is suppressed, and setup labels test and real-download
  stages. CI now includes macOS/Python 3.12 as well as Linux.

To resume from the launcher branch, without recloning or reinstalling Homebrew:

```bash
cd ~/Projects/suzy-ai-mac
git pull --ff-only origin feature/mac-local-launcher
bash scripts/setup-mac.sh && bash scripts/start-mac.sh
```
