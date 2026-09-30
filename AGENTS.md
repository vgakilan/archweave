# Project: Requirement to Diagram

## Goal

Turn parsed Markdown software requirements into reviewable diagrams and a
short written companion for business analysts, customers, and other readers.

## Workflow

Parsed Markdown → evidence-backed Requirement Model → validation → view plan
→ Mermaid → local Mermaid CLI → SVGs and written companion.

Use `.agents/skills/requirement-review/SKILL.md` and
`prompts/requirement_review.md`. In a Codex session, invoke the skill directly
with `$requirement-review`. `scripts/run_pipeline.py` is the noninteractive
terminal entry point; it uses the signed-in Codex CLI for extraction and view
planning.
The Markdown produced by AnyDoc is the sole source for requirement facts. Do
not compare it with the original document.

## Rules

1. The full Requirement Model is the source of truth. Extract only stated facts.
2. Never generate Mermaid directly from raw requirements.
3. Separate interpretation, view planning, and rendering.
4. Choose architecture, flowchart, or sequence per reader question and only
   when the model supports it. One clear view is enough when it answers the
   question; otherwise use focused views.
5. Do not invent components, technologies, protocols, relationships, process
   transitions, or message order. Report insufficiency instead.
6. Preserve significant facts outside the diagrams in the written companion.
7. Rendering failures must fail the process. Keep generated artifacts under
   `diagrams/` and business logic outside CLI scripts.

## Implementation

Use Python 3.12+. Node.js is permitted for the repository's local Mermaid CLI.
`schemas/requirement.schema.json` defines the model contract. Validate with
`diagram_generator.requirement_model.load_requirement_model`, and generate with
`scripts/generate_review.py`. Test with pytest and verify rendered SVGs.
