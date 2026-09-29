# Requirement to Diagram

A Python 3.12+ prototype for turning software requirements into reviewable
architecture diagrams. The structured JSON diagram is the source of truth;
Mermaid and SVG are generated artifacts. The normal requirement-analysis path
uses Codex with repository prompts and does not require an API key.

## Architecture

Requirement source → Requirement Analyzer → Diagram model → Schema/domain
validation → Diagram Planner (optional focused views) → Mermaid generator →
local Mermaid CLI renderer → SVG.

Analysis decides *what the requirement states*. Planning chooses *which of
those facts to show and how to group them*. Rendering converts the validated
selection to Mermaid and SVG. See [architecture](docs/architecture.md).

## Setup

Install Python 3.12 or newer and Node.js 22.13 or newer. From the repository
root on Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm ci
npm run mermaid:version
```

If `py -3.12` is unavailable, select any installed Python 3.12+ version when
creating `.venv`. `npm ci` installs the official Mermaid CLI and local Iconify
packs from `package-lock.json`; it does not install a global `mmdc`.

## Current workflow

1. Supply a `.txt`, readable `.pdf`, or extracted PDF text requirement. Read
   `AGENTS.md`, `prompts/requirement_analyzer.md`, and the
   [diagram schema](schemas/diagram.schema.json).
2. Use Codex to extract only supported components and relationships into
   `diagrams/model/<name>.generated.json`. The reusable instructions are in
   [generate_diagram.md](prompts/generate_diagram.md). No OpenAI API call is
   needed for this path.
3. Validate the JSON with `diagram_generator.loader.load_diagram`. The loader
   applies JSON Schema and domain checks for IDs, groups, and edge references.
4. For a small model, run `scripts/generate_diagram.py`. For a larger model,
   define a plan under `diagrams/plans/` using
   [diagram_planner.md](prompts/diagram_planner.md), then run
   `scripts/generate_views.py`. A plan filters existing facts; it cannot add
   relationships.
5. Inspect the `.mmd` and `.svg` under `diagrams/source/` and
   `diagrams/rendered/`, verify SVG parsing, and run pytest.

The full model remains intact when focused views are generated. Diagram
directions and view grouping are presentation choices, not inferred
communication paths.

## Structured model

A diagram has `title`, `diagram_type` (`architecture` or `flowchart`),
`direction` (`LR`, `RL`, `TB`, or `BT`), `nodes`, and `edges`; `groups` is optional.
An edge names existing `source` and `target` IDs and may have a semantic
`label` and separately stated `protocol`. Node IDs must be unique.

Supported node types are `actor`, `application`, `service`, `gateway`,
`database`, `external_system`, and `message_broker`. A node may reference a
group. Groups have unique IDs and labels, with at most one nested level.
Grouping expresses containment or a view layer, not a communication edge.

Node `icon` is optional presentation metadata. `generic` selects a local
Lucide icon for the node type. An explicitly named technology may use an
available local `simple-icons:<name>` icon. Missing icons fall back to a
generic icon or the normal Mermaid node shape; diagrams remain valid without
icons. Icon choices never justify a component or technology claim.

## Usage examples

Generate and render a curated deterministic model:

```powershell
.\.venv\Scripts\python.exe scripts\generate_sample.py
.\.venv\Scripts\python.exe scripts\generate_diagram.py diagrams\model\order_processing.generated.json
```

Generate focused banking views from the existing full model:

```powershell
.\.venv\Scripts\python.exe scripts\generate_views.py diagrams\model\banking_system_requirement.generated.json diagrams\plans\banking_system_requirement.json
```

Ask Codex to analyze a new requirement:

> Follow `prompts/generate_diagram.md` for `requirements/my_requirement.txt`.
> Treat that file as the sole source of architectural facts. Generate and
> validate the model, Mermaid source, and SVG.

For a larger model, ask Codex to follow `prompts/diagram_planner.md` after the
full model validates. See [testing](docs/testing.md) for verification commands.

## Optional OpenAI analyzer

`src/diagram_generator/openai_analyzer.py` implements the analyzer contract
with the OpenAI Responses API and Structured Outputs. It is optional and is
not used by the Codex workflow or normal tests. To run its sample script,
set `OPENAI_API_KEY` in the environment; `OPENAI_MODEL` optionally overrides
the default `gpt-4.1-mini`. The script writes
`diagrams/model/sample.generated.json` and does not overwrite the curated
reference model. Do not commit keys or confidential requirements.

## Testing and current limits

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run mermaid:version
```

The prototype supports Mermaid SVG only. Codex currently performs the normal
requirement analysis; PDF quality depends on readable source content. View
plans are predefined, and Mermaid can stack disconnected nodes poorly. There
is no draw.io export, production agent framework, or organization-specific
governance. See [limitations](docs/limitations.md) and
[security](docs/security.md) before sharing inputs or outputs.
