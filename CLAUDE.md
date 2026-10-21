# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Shared connector + observability library for the HRB chatbot microservices split. One Python package, ten independently-installable extras (`observability`, `db`, `cache`, `llm`, `mcp`, `storage`, `web`, `auth`, `email`, `ci`), extracted from `hrb_chatbot_v2`'s own `common/clients/` folders. A service installs only the extras it actually needs - `pip install "hrb-common-libs[db,cache]"` never pulls in `openai`, `mcp`, or `boto3`.

Full design rationale, the dependency matrix (which service needs which extra), and the `pyproject.toml` sketch live in `hrb_chatbot_v2`'s own `docs/dev-reference/common-libs-connectors/` doc set (Overview/Spec/Architecture/Design/Decisions) - read that before changing anything here. This repo implements that design; it doesn't re-derive it.

Python 3.12 only, matching every consuming service.

## Commands

```bash
# install for local dev, all extras
pip install -e ".[observability,db,cache,llm,mcp,storage,web,auth,email,ci]"

# install for local dev, one extra
pip install -e ".[observability,db]"

# run tests
pytest -v

# build
python -m build
```

## Architecture

Every extra follows the same `Base*Client` ABC + Gateway pattern already proven in `hrb_chatbot_v2`: an abstract base class per backend type, a concrete implementation per provider, and a singleton Gateway that builds/caches clients lazily. Calling code never branches on provider outside the Gateway - that's what makes swapping Pinecone for ChromaDB, or OpenAI for OpenRouter, a config change in the consuming service, not a code change here.

`observability` is the one extra every other extra depends on (logging, request_id propagation, retry/backoff, circuit breaker) - installing `db` or `llm` pulls it in automatically. No extra depends on any other extra besides `observability`.

### Package layout

```
src/hrb_common/
  observability/   logger, request_id middleware, retry decorator, circuit breaker, settings/secrets helper
  db/              Postgres Base*Client + Gateway (from hrb_chatbot_v2's db_client/)
  cache/           Redis connector (from cache_client/)
  llm/             LLM provider Gateway - OpenAI/OpenRouter/Bedrock + embeddings (from llm_client/)
  mcp/             MCP tool-call client (from mcp_client/)
  storage/         S3 connector (from storage_client/)
  web/             Tavily web-search connector (from web_client/)
  auth/            OAuth2 client-credentials + JWT validation (from auth_client/)
  email/           SES connector (from email_client/)
  ci/              GitHub Actions client (from ci_client/) - platform-only, no core-business service depends on this
```

## Spec-Driven Development

Same convention as `hrb_chatbot_v2`: no separate `specs/` folder - a spec is a `**Spec:**` block written into a phase's own bullet in `ROADMAP.md`'s `## Phases` section, before that phase's code starts. `.claude/scripts/spec_gate.py` blocks a `Write`/`Edit` under `src/hrb_common/**` unless `ROADMAP.md` has at least one open phase with a written spec.

**Four working norms, same as `hrb_chatbot_v2`:**
- **One task at a time.** Finish one extra/phase, report, wait for review.
- **Flag, don't fix.** Something noticed outside scope gets a one-line note, not an unprompted fix.
- **Nothing gets pushed without the user's own review and explicit go-ahead first.**
- **Behavior must not change during extraction.** Every extracted client's existing test (ported from `hrb_chatbot_v2`'s `tests/hrb_chatbot/common/clients/`) must pass unmodified - this repo's first job is a faithful move, not a redesign.

**Available skills**: `session-start`, `delivery-note`, `spec-new`, `spec-implement`.
**Subagents**: `.claude/agents/implementer.md`, `.claude/agents/code-reviewer.md`.
