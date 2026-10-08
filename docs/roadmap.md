# Roadmap

## 0.1 - nervous system

- [x] public core repository
- [x] private local home
- [x] app registry
- [x] generic event protocol
- [x] timeline protocol
- [x] local event server
- [x] local CLI
- [ ] Appliance adapter
- [ ] POP//CONTEXT adapter

## 0.2 - local mind

- [x] model adapter interface
- [x] adapter for an independently installed local OpenAI-compatible runtime
- [ ] machine-aware model selection
- [ ] local prompt / response provenance
- [x] hard loopback-only transport with no cloud fallback

## 0.3 - memory

- [x] explicitly approved private document store
- [x] bounded lexical retrieval with SQLite FTS5
- [ ] semantic embeddings
- [ ] approved corrections
- [x] explicit memory provenance
- [ ] export / backup

## 0.4 - current world

- [ ] research request protocol
- [ ] open web search adapter
- [ ] primary-source preferences
- [ ] source freshness
- [ ] cached citations
- [ ] offline degradation

## 0.5 - creative learning

- [ ] approved Appliance performance examples
- [ ] personal sound corpus
- [ ] audiovisual associations
- [ ] dataset versioning
- [ ] evaluate fine-tuning only after the dataset exists

## Rule

Do not train a personality before we have earned a dataset worth training on.

## v0.3 integration

- [x] stateless `/v1/chat` API; memory opt-in per request
- [x] safe inference failure handling and request/response limits
- [x] same-origin local API protection
- [x] synthetic tests and Python 3.11–3.13 CI

Prompt/response provenance is returned per request, not persisted. Machine-aware
selection, approved corrections, semantic embeddings and export tooling remain
future work. See [local chat](local-chat.md).
