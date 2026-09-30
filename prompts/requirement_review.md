# Requirement review workflow

Use the existing parsed Markdown as the sole source of requirement facts. Do not compare it with the original document. Read `schemas/requirement.schema.json` before writing a model. Save the full model to `diagrams/model/<name>.requirement.json`.

## Extract facts

- Create nodes only for stated actors or components. Keep generic names generic and distinct names distinct. Use the supported node types only where they are accurate.
- Create an edge only when its endpoints and direction are stated. Preserve the stated action and protocol; do not infer a protocol from words such as "API" or "web".
- Create a process when the Markdown states steps or decisions. A transition needs evidence for its order or branch. Never connect steps solely to make a continuous chart. Put a condition on a transition only when stated.
- Give edges `scenario` and `sequence` only when a specific scenario and message order are supported. Sequence numbers express the stated order, not the order in which items happen to appear in a feature list.
- Put important rules that do not fit a diagram in `statements`. Put material ambiguities and missing details in `open_points`; do not turn them into facts.
- Set `scope` to `future` for proposed improvements. Do not combine future and current facts in a view.
- Give every fact evidence with a Markdown section and a short exact excerpt from the Markdown. If an excerpt cannot be found, revise or omit the fact. Empty arrays are valid when that kind of fact is absent.

Validate with `diagram_generator.requirement_model.load_requirement_model`. If the Markdown cannot support a useful model or view, report insufficiency rather than inventing facts.

## Choose views

After model validation, decide what each audience question needs:

| Question | View type | Required facts |
|---|---|---|
| What are the main parts and stated connections? | `architecture` | Nodes and optional edges |
| What happens, including branches and outcomes? | `flowchart` | One process with explicit steps and transitions |
| Who exchanges messages in what order? | `sequence` | At least two edges with one scenario and distinct stated sequence positions |

Use one view when it answers the reader's question clearly. Add focused views for distinct questions or a crowded overview. Do not force every fact into a diagram. A plan lives at `diagrams/plans/<name>.review.json` and has a `views` array. Each view has exactly `name`, `title`, `purpose`, `type`, `scope`, `fact_ids`, and `direction`. `name` is a unique filesystem-safe ID; `direction` is `LR`, `RL`, `TB`, or `BT` (ignored for sequence). An architecture view selects node IDs and optional edge IDs, including both endpoints of every selected edge. A flowchart selects one process ID. A sequence view selects ordered edge IDs from one scenario. Select only facts from the same scope.

## Render and review

Run `python scripts/generate_review.py <model-json> <plan-json>`. It validates the model and every view, writes Mermaid to `diagrams/source/`, renders SVG in `diagrams/rendered/`, and writes a companion report in `diagrams/reports/`. Rendering failures fail the run. Inspect every SVG for legibility. The companion lists view purposes, facts outside the views, and unresolved points. Check that diagrams and written claims remain supported by the Markdown.
