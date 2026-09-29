# End-to-end requirement-to-diagram workflow

## Input

The user supplies a path to one requirement file. Accept plain `.txt`, text extracted from a PDF, or a `.pdf` that you can read. Treat that file as the sole source of architectural facts. If the file is missing or a PDF cannot be read reliably, request readable text rather than guessing from its name.

Use Codex itself as the Requirement Analyzer. Do not call the OpenAI API, run `scripts/analyze_sample.py`, or require `OPENAI_API_KEY`.

## Workflow

1. Read `AGENTS.md`, `prompts/requirement_analyzer.md`, and `schemas/diagram.schema.json` before analyzing the supplied file. Follow their current constraints and supported types.
2. Read the supplied requirement. For a PDF, extract its text and inspect relevant architecture figures or tables when text extraction omits them. If supplied extracted text has page markers, retain those references for the report. Identify the source sections used. Do not treat examples or existing diagram models as evidence about this requirement.
3. Analyze the requirement into a concise architecture or flowchart model. Include only stated actors, components, stores, boundaries, and directed relationships. Preserve generic terminology and ambiguity; omit unsupported technology, protocols, database products, APIs, queues, and calls. For large documents, select the main architecture unless the user specifies a narrower view.
4. Write a JSON model under `diagrams/model/`. Use a user-specified model filename when provided; otherwise use `diagrams/model/<source-stem>.generated.json`, with a filesystem-safe source stem and any trailing `.extracted` removed. Do not overwrite a curated reference model. Include `groups` only when the requirement supports boundaries or layers. Keep `icon` optional and separate from architectural facts.
5. Validate the saved JSON with `diagram_generator.loader.load_diagram`. Resolve every edge endpoint to a node and every group reference to a group. Fix errors in the model before rendering. If the current schema or taxonomy cannot express a detail faithfully, use the existing types only where they remain accurate, omit the unrepresentable detail if needed, and report the gap. Do not change the schema automatically.
6. From the repository root, run `python scripts/generate_diagram.py <model-json>`. This existing pipeline loads and validates the JSON, writes `diagrams/source/<model-stem>.mmd`, and renders `diagrams/rendered/<model-stem>.svg` with the local Mermaid CLI. Do not generate Mermaid directly from raw requirement text.
7. If the validated model needs focused views, follow `prompts/diagram_planner.md`, save a predefined plan under `diagrams/plans/`, and run `python scripts/generate_views.py <model-json> <plan-json>`. Keep the full model unchanged and use only its exact relationships in every view.
8. Verify each `.mmd` exists, each `.svg` exists and is non-empty, and every SVG parses with Python's `xml.etree.ElementTree`. Rendering errors must fail the workflow; do not report success if the CLI fails.
9. Run `python -m pytest` from the repository root. Report the result and any failures. Do not add runtime application logic merely to complete a requirement analysis.

## Presentation policy

Semantic correctness comes before visual styling. Icons are optional metadata; diagrams must remain valid without them. Use `generic` icons for generic concepts. Use a vendor icon only when the requirement explicitly names that technology and the local icon pack contains it. An icon must never supply evidence for a node's type, label, or technology. Do not invent relationships to improve layout.

## Verification checklist

- [ ] JSON conforms to the schema and passes domain validation.
- [ ] Every edge source and target names an existing node; group references resolve.
- [ ] Mermaid generation succeeds from the validated model.
- [ ] Any planned view selects only source-model nodes and exact source-model relationships.
- [ ] SVG rendering succeeds with the local Mermaid CLI.
- [ ] SVG exists, is non-empty, and parses as XML.
- [ ] `python -m pytest` passes, or failures are reported accurately.

## Final report

Report the input path and source sections used; model, Mermaid, and SVG paths; extracted nodes, groups, and relationships; ambiguity and assumptions avoided; schema or taxonomy gaps; validation and render results; pytest result; and any remaining limitations. Distinguish explicit source facts from any presentation defaults such as layout direction or icons.
