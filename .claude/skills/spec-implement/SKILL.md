# Implement a spec'd phase

Execute one phase from `ROADMAP.md` that already has a written `**Spec:**`
block. Stay inside that spec's declared scope - a phase touching one extra
does not also refactor another.

## Steps

1. Read the phase's `**Spec:**` block in full.
2. If it's an extraction phase: copy the source file(s) from the path the
   spec names (a local clone of `hrb_chatbot_v2`, or the file content the
   user pastes), adapt imports to `src/hrb_common/<extra>/`, port the
   matching test file(s), run them, confirm they pass unmodified in
   behavior.
3. If it's new code (the observability extra): implement against the
   spec's API surface, write new tests.
4. Run `pytest -v` for the whole repo, not just the new files - confirm no
   regression in extras already extracted.
5. Flip the phase's checkbox to `- [x]` and update the "Status at a
   glance" table's Status column to "✅ Done" only after tests pass.
6. Produce a delivery note (`/delivery-note`).
