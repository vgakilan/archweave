# Testing and acceptance

Run these commands from the repository root after installing Python and npm
dependencies as described in the README.

## Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

Pytest covers schema and domain validation, model loading, Mermaid generation,
grouping, icon fallback, view filtering, renderer failures, and the optional
analyzer with mocked API responses. Normal tests do not require network access
or an OpenAI key. `git diff --check` checks tracked changes; review untracked
files separately before publishing.

## Mermaid CLI verification

```powershell
npm run mermaid:version
```

This uses the local `@mermaid-js/mermaid-cli` dev dependency. A version result
alone does not prove browser rendering works; run a real generation command
below as a smoke test.

## Deterministic model generation

The curated sample JSON is the source for a reproducible Mermaid and SVG
render. The Python script does not re-analyze the requirement text.

```powershell
.\.venv\Scripts\python.exe scripts\generate_sample.py
.\.venv\Scripts\python.exe scripts\generate_diagram.py diagrams\model\order_processing.generated.json
.\.venv\Scripts\python.exe scripts\generate_diagram.py diagrams\model\hms.generated.json
.\.venv\Scripts\python.exe scripts\generate_diagram.py diagrams\model\hms_backend.generated.json
.\.venv\Scripts\python.exe scripts\generate_views.py diagrams\model\banking_system_requirement.generated.json diagrams\plans\banking_system_requirement.json
```

The generic command validates its JSON model, writes a `.mmd` file, and
renders an SVG. The view command validates every projection against the full
model before rendering. Rendering errors fail the command.

## Codex end-to-end check

For a new requirement, ask Codex to follow
`prompts/generate_diagram.md` with the file path. Check its extracted model
against the source, especially every directed edge, protocol, database
engine, and external system. Have Codex run the generic generation command,
parse the SVG, and run pytest. For a large model, review a plan using
`prompts/diagram_planner.md` before generating focused views. This path does
not use the OpenAI API.

## Manual SVG inspection

Open each SVG in a browser or viewer. Confirm text is legible, groups do not
imply unsupported boundaries, no node is clipped, and the flow and external
systems are easy to locate. Check disconnected views carefully: Mermaid may
stack nodes despite an `LR` preference. Do not add a communication edge just
to improve layout.

## Acceptance checklist

- [ ] Requirement source has been reviewed and is approved for this workspace.
- [ ] JSON passes schema and domain validation; node, edge, and group references resolve.
- [ ] Each planned view uses only source-model nodes and exact source-model edges.
- [ ] Mermaid source is generated from the validated model.
- [ ] SVG rendering succeeds; every SVG is non-empty and parses as XML.
- [ ] Manual SVG inspection finds no clipping or misleading visual implication.
- [ ] Pytest passes and the local Mermaid CLI reports its version.
- [ ] Source requirements, models, and SVGs are approved before GitHub publication.
