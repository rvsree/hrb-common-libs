# hrb-common-libs

Shared connector + observability library for the HRB chatbot microservices split.

Ten independently-installable extras, mapped 1:1 onto `hrb_chatbot_v2`'s existing `common/clients/` folders: `observability`, `db`, `cache`, `llm`, `mcp`, `storage`, `web`, `auth`, `email`, `ci`. A service installs only what it needs:

```bash
pip install "git+https://github.com/rvsree/hrb-common-libs.git@v0.1.0#egg=hrb-common-libs[db,cache]"
```

Full design doc: `hrb_chatbot_v2`'s `docs/dev-reference/common-libs-connectors/`.

Status: scaffolding only - no extraction has happened yet. See `ROADMAP.md`.
