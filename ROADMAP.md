# hrb-common-libs Roadmap

Phase-by-phase plan and history, same convention as `hrb_chatbot_v2`'s `docs/agent-reference/RAG-ROADMAP.md`. A phase gets a `**Spec:**` block written before its code starts (`/spec-new`), and its checkbox flips to `- [x]` once implemented and verified.

## Status at a glance

| Phase | Title | Status | Spec |
|---|---|---|---|
| 1 | observability extra | ✅ Done | written |
| 2 | db extra | 📋 Planned | not yet written |
| 3 | cache extra | 📋 Planned | not yet written |
| 4 | llm extra | 📋 Planned | not yet written |
| 5 | mcp extra | 📋 Planned | not yet written |
| 6 | storage extra | 📋 Planned | not yet written |
| 7 | web extra | 📋 Planned | not yet written |
| 8 | auth extra | 📋 Planned | not yet written |
| 9 | email extra | 📋 Planned | not yet written |
| 10 | ci extra | 📋 Planned | not yet written |

## Phases

- [x] **Phase 1 (done) — observability extra.** New code (not an extraction): logger, request_id context, retry/backoff decorator, circuit breaker (generalizing `hrb_chatbot_v2`'s Phase 185 MCP-specific implementation), secrets-resolution helper. Every other extra depends on this one. Full requirements in `hrb_chatbot_v2`'s `docs/dev-reference/nfr-platform-components/`.
  - **Spec:**
    - **Context:** first real code in this repo - every other extra (`db`, `cache`, `llm`, ...) depends on this one, so it has to exist before any extraction phase starts.
    - **Source:** not an extraction. The retry/circuit-breaker semantics generalize the real, live pattern in `hrb_chatbot_v2`'s `src/hrb_chatbot/ai/rag_pipeline/tools/mcp_tools/__init__.py` (`MCP_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 2`, `MCP_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 10`, verified against the code directly, not assumed) - that implementation is Postgres-backed and MCP-specific; this one is in-memory and generic, same failure-threshold + cooldown semantics, not a literal port.
    - **API surface:**
      - `get_logger(name: str) -> logging.Logger` - structured JSON-capable logger, matching `hrb_chatbot_v2`'s `common/logging/logger.py` shape.
      - `log_backend_call(logger, service, operation, **context)` - context manager, direct port of `hrb_chatbot_v2`'s `common/logging/call_logger.py` (already generic, no change needed beyond the import path).
      - `RequestContext` - a contextvar-backed holder for the current `request_id`, with `set_request_id()`/`get_request_id()`.
      - `with_retry(max_attempts=3, backoff_base_seconds=0.5)` - decorator, built on `tenacity`.
      - `CircuitBreaker(name, failure_threshold=2, cooldown_seconds=10)` - in-memory, thread-safe counter + last-failure timestamp; `__enter__`/`__exit__` raises a typed `CircuitOpenError` if tripped, records success/failure on exit otherwise.
      - `read_secret(key: str, default: str | None = None) -> str | None` - thin wrapper, same semantics as `hrb_chatbot_v2`'s `common.config.settings.read_setting`.
    - **Behavior parity:** N/A (new code) except `log_backend_call`, which must behave identically to the existing `call_logger.py` - port its existing test file unmodified.
    - **Out of scope:** no Secrets Manager SDK call yet (stub reading from env only - real Secrets Manager integration is a later phase once a consuming service actually needs it in AWS, not before). No distributed/shared circuit-breaker state (in-memory per-process only, matching the per-process assumption; a future phase may back it with Redis once `cache` extra exists).
    - **Open questions:** none blocking.

- [ ] **Phase 2 (planned) — db extra.** Extraction of `hrb_chatbot_v2`'s `common/clients/db_client/` into `src/hrb_common/db/`. Behavior must not change - every ported test must pass unmodified.

- [ ] **Phase 3 (planned) — cache extra.** Extraction of `cache_client/`.

- [ ] **Phase 4 (planned) — llm extra.** Extraction of `llm_client/` (OpenAI/OpenRouter/Bedrock + embeddings).

- [ ] **Phase 5 (planned) — mcp extra.** Extraction of `mcp_client/`.

- [ ] **Phase 6 (planned) — storage extra.** Extraction of `storage_client/`.

- [ ] **Phase 7 (planned) — web extra.** Extraction of `web_client/` (Tavily).

- [ ] **Phase 8 (planned) — auth extra.** Extraction of `auth_client/` (OAuth2 client-credentials, JWT validation).

- [ ] **Phase 9 (planned) — email extra.** Extraction of `email_client/` (SES).

- [ ] **Phase 10 (planned) — ci extra.** Extraction of `ci_client/` (GitHub Actions). Platform-only - no core-business service should ever declare this extra.
