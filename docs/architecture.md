# Architecture

```text
Source document → AnyDoc Markdown → Requirement Model → validation
                                              ↓
                                      per-view plan
                                              ↓
                               Mermaid → local CLI → SVGs
                                              ↓
                                  written companion
```

`document_parser.py` saves Markdown. `workflow.py` invokes the read-only Codex
CLI twice: first to extract facts, then to choose views after model validation.
Codex interprets only the Markdown, following `prompts/requirement_review.md`;
it does not compare the parsed text with the original document. The full JSON
Requirement Model records nodes,
edges, processes, statements, open points, scope, and exact evidence excerpts.
Nodes and edges describe architecture; processes and statements capture
behavior and important facts outside that graph. `requirement_model.py` checks
the JSON Schema, cross-references, sequence positions, and excerpt presence in
the Markdown.

The planner chooses a diagram type for each reader question after validating the
full model. Architecture views select nodes and edges. Flowcharts
select an explicitly described process. Sequence views select ordered messages
from one stated scenario. `review_package.py` rejects unsupported selections
and mixed current/future views before rendering. A view changes presentation,
never the source facts.

`mermaid.py` handles architecture diagrams; `review_package.py` handles process
and sequence syntax. `renderer.py` invokes the repository's local official
Mermaid CLI and fails on an unsuccessful or empty render. The package generator
also parses each SVG as XML. Mermaid files, SVGs, and the written companion
live under `diagrams/`; the companion lists facts outside the views and open
points with an evidence index.
