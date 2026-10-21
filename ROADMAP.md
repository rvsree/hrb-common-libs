# hrb-common-libs Roadmap

Phase-by-phase plan and history, same convention as `hrb_chatbot_v2`'s `docs/agent-reference/RAG-ROADMAP.md`. A phase gets a `**Spec:**` block written before its code starts (`/spec-new`), and its checkbox flips to `- [x]` once implemented and verified.

## Status at a glance

| Phase | Title | Status | Spec |
|---|---|---|---|
| 1 | observability extra | 📋 Planned | not yet written |
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

- [ ] **Phase 1 (planned) — observability extra.** New code (not an extraction): logger, request_id middleware, retry/backoff decorator, circuit breaker (generalizing `hrb_chatbot_v2`'s Phase 185 MCP-specific implementation), secrets-resolution helper. Every other extra depends on this one. Full requirements in `hrb_chatbot_v2`'s `docs/dev-reference/nfr-platform-components/`.

- [ ] **Phase 2 (planned) — db extra.** Extraction of `hrb_chatbot_v2`'s `common/clients/db_client/` into `src/hrb_common/db/`. Behavior must not change - every ported test must pass unmodified.

- [ ] **Phase 3 (planned) — cache extra.** Extraction of `cache_client/`.

- [ ] **Phase 4 (planned) — llm extra.** Extraction of `llm_client/` (OpenAI/OpenRouter/Bedrock + embeddings).

- [ ] **Phase 5 (planned) — mcp extra.** Extraction of `mcp_client/`.

- [ ] **Phase 6 (planned) — storage extra.** Extraction of `storage_client/`.

- [ ] **Phase 7 (planned) — web extra.** Extraction of `web_client/` (Tavily).

- [ ] **Phase 8 (planned) — auth extra.** Extraction of `auth_client/` (OAuth2 client-credentials, JWT validation).

- [ ] **Phase 9 (planned) — email extra.** Extraction of `email_client/` (SES).

- [ ] **Phase 10 (planned) — ci extra.** Extraction of `ci_client/` (GitHub Actions). Platform-only - no core-business service should ever declare this extra.
