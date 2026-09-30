# Requirement to Diagram

Convert a software requirement into a review package: focused diagrams and a
short written explanation. The evidence-backed Requirement Model, with nodes
and edges, is the source of truth. Mermaid and SVG are generated from planned
views of that model.

## Setup

Use Python 3.12+, Node.js 22.13+, and an installed, signed-in Codex CLI. On
Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm ci
New-Item -ItemType Directory -Force requirements | Out-Null
```

Place the source document in `requirements/` before running a review. This
directory and the generated `diagrams/` directory are ignored by Git; the
workflow creates output directories as needed.

## Workflow

In Codex, open this repository and type:

```text
$requirement-review
```

If several documents are in `requirements/`, Codex will ask which one to use.
You can also name it in the same message, such as
`$requirement-review requirements/my_requirement.docx`. The skill analyzes the
parsed Markdown in the current Codex session and produces the review package.

For a noninteractive terminal run, use one command with a requirement document
or already parsed Markdown:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py requirements\my_requirement.docx
```

The command parses the document when needed, asks the signed-in Codex CLI to
extract a model and plan views, validates both, writes Mermaid to
`diagrams/source/`, renders SVGs in `diagrams/rendered/`, and writes the
companion in `diagrams/reports/`. Intermediate JSON lives in `diagrams/model/`
and `diagrams/plans/`. Analysis and planning send the parsed Markdown to Codex;
the CLI uses its existing sign-in, so no separate API key is needed. A
validation or rendering failure stops the command.

The [skill](.agents/skills/requirement-review/SKILL.md) and
[workflow prompt](prompts/requirement_review.md) define interpretation rules.
To render an already prepared model and plan without a Codex call, use:

```powershell
.\.venv\Scripts\python.exe scripts\generate_review.py diagrams\model\<name>.requirement.json diagrams\plans\<name>.review.json
```

The model format is defined in [the schema](schemas/requirement.schema.json).
See [architecture](docs/architecture.md), [testing](docs/testing.md),
[limitations](docs/limitations.md), and [security](docs/security.md).

## Document parsing

```powershell
.\.venv\Scripts\python.exe scripts\parse_document.py requirements\my_requirement.docx
```

The parser saves Markdown under `requirements/parsed/` by default. AnyDoc
converts supported formats locally. Scanned PDFs need OCR; optional
`--ocr hosted` sends the document to Firecrawl Parse. Parsing must succeed
before analysis. The analyzer treats the resulting Markdown as authoritative.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run mermaid:version
```
