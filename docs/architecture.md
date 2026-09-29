# Architecture

The pipeline is:

```text
Requirement source
  → Requirement Analyzer
  → Diagram model
  → JSON Schema and domain validation
  → Diagram Planner (optional focused views)
  → Mermaid generator
  → local Mermaid CLI renderer
  → SVG
```

## Semantic model

A requirement source is a plain-text file, readable PDF, or extracted PDF
text. The Requirement Analyzer interprets only that source. Codex is the
normal analyzer in the current workflow, following
`prompts/requirement_analyzer.md`; the optional OpenAI-backed implementation
conforms to the same analyzer contract. Neither rendering nor planning
interprets raw requirement text.

`src/diagram_generator/models.py` defines immutable `Diagram`, `Node`,
`Edge`, and `Group` values. `schemas/diagram.schema.json` defines the JSON
contract. `loader.py` checks that contract and constructs the domain model;
domain checks cover unique IDs, group references and nesting, and edge
endpoints. The saved full JSON model under `diagrams/model/` is the source of
truth. Labels and protocols belong to edges only when the requirement states
them. Group membership in the full model reflects supported boundaries or
layers.

## Presentation and planning

`src/diagram_generator/planner.py` reads a predefined view plan from
`diagrams/plans/`. Each view names included source node IDs and exact source
relationships, its purpose, view-only groups, preferred direction, primary
flow, external-system boundary group, and a maximum node count. Validation
rejects missing nodes, altered or invented edges, invalid flow sequences,
and overlarge views before rendering starts. The planner projects a new
in-memory Diagram without modifying the full model.

View groups and direction control presentation. They do not assert extra
communication. A view can deliberately omit nodes or leave nodes disconnected
when the source does not state a relationship. The banking plan demonstrates
context, services, infrastructure, and messaging views.

## Mermaid and SVG

`mermaid.py` turns only a validated Diagram into deterministic Mermaid text.
It renders groups as subgraphs, assigns classes by node type, preserves edge
labels and protocols, and optionally resolves icons from locally installed
Iconify packs. `renderer.py` invokes the repository's
`node_modules/.bin/mmdc` through `subprocess`, captures stdout and stderr,
and raises on failure or empty SVG. It does not use a global Mermaid CLI.

`pipeline.py` coordinates validation, Mermaid writing, and SVG rendering.
The scripts in `scripts/` only provide command-line entry points. Generated
source files live in `diagrams/source/`; rendered SVGs live in
`diagrams/rendered/`.
