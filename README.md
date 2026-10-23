# hrb-common-libs

Shared connector + observability library for the HRB chatbot microservices split.

Ten independently-installable extras, mapped 1:1 onto `hrb_chatbot_service`'s original `common/clients/` folders: `observability`, `db`, `cache`, `llm`, `mcp`, `storage`, `web`, `auth`, `email`, `ci`. A service installs only what it needs:

```bash
pip install "git+https://github.com/rvsree/hrb-common-libs.git@v0.4.0#egg=hrb-common-libs[db,cache]"
```

Full design doc: `hrb_chatbot_service`'s `docs/dev-reference/common-libs-connectors/`.

**Status, 2026-10-23: all 17 phases built, tagged v0.4.0, in real production use** by every other repo in this split (`hrb_api_gateway_service`, `hrb_platform_components`, `rag_ingestion_service`, `rag_retrieval_service`) - one git-tag-pinned version for everyone, never a floating dependency. Confirmed live: `Secrets Manager + request_id middleware` (Phase 17) is in real use by `rag_ingestion_service`'s own Lambda, confirmed working in production.
