---
name: requirement-review
description: Generate reviewable architecture, flowchart, or sequence diagrams and a written report from a requirement document in this repository.
---

# Requirement review

When the user invokes this skill, use an explicitly named requirement document
if provided. Otherwise inspect files directly under `requirements/`, excluding
`parsed/`. If exactly one source document is present, use it. If several are
present and context does not identify one, ask the user to choose a filename.
Do not guess from file names or silently process every document.

Act as the analyzer and planner in this Codex session. Do not call
`scripts/run_pipeline.py`, because that starts another Codex session.

1. For a source document, run `scripts/parse_document.py <document>` and read
   the saved Markdown. For an already parsed Markdown file, use it directly.
   Treat only that Markdown as evidence; do not compare it with the original.
2. Follow [the repository workflow](../../../prompts/requirement_review.md) and
   [the requirement schema](../../../schemas/requirement.schema.json). Write
   `diagrams/model/<name>.requirement.json` with explicit nodes and edges,
   plus supported processes, statements, and open points. Preserve exact
   Markdown excerpts. Omit unsupported facts.
3. Validate the model with
   `diagram_generator.requirement_model.load_requirement_model`. Then choose
   one or more focused views based on the reader's questions. Write
   `diagrams/plans/<name>.review.json` using only validated fact IDs.
4. Run `scripts/generate_review.py <model-json> <plan-json>`. Inspect each SVG
   and the written companion under `diagrams/`. Fix unsupported or unreadable
   views without inventing facts. A render failure is a task failure.
5. Tell the user where the model, plan, diagrams, and report are. Report any
   ambiguity or limitation that needs their review.