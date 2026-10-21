# Write a new spec

This repo has no separate `specs/` folder - a spec is a `**Spec:**` block
written into the target phase's own bullet in `ROADMAP.md`'s `## Phases`
section, **before** that phase's code starts. Same convention as
`hrb_chatbot_v2`.

## Steps

1. Find the target phase's `- [ ]` bullet in `ROADMAP.md`'s `## Phases` section.
2. Append a nested `**Spec:**` sub-list to that bullet:

   ```
   - **Spec:**
     - **Context:** why this phase, what triggered it.
     - **Source:** which hrb_chatbot_v2 file(s) this extracts from, if any.
     - **API surface:** the public classes/functions this extra exports.
     - **Behavior parity:** which existing hrb_chatbot_v2 tests must pass
       unmodified against the extracted code (N/A for new code like the
       observability extra).
     - **Out of scope:** what this phase deliberately does not do.
     - **Open questions:** anything needing a decision before/during implementation.
   ```

3. Set that phase's checkbox to `- [ ]` (not started) if it isn't already.
4. Do not write any implementation code in this step. Report the spec back
   to the user for review before anything in `src/` changes.
