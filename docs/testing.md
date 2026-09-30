# Testing

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run mermaid:version
git diff --check
```

Pytest covers document parsing, requirement evidence and reference validation,
view selection rules, orchestration, Codex CLI error handling, report
generation, and renderer failure behavior. It uses temporary fixtures and
mocked model calls and rendering, so routine tests need no API key or browser
launch.

For an end-to-end check, run `scripts/run_pipeline.py` with a requirement
document, or render a prepared model and plan with `scripts/generate_review.py`.
Confirm every SVG is
nonempty, parses as XML, and clearly answers its view's stated purpose. Check
the written companion for omitted facts, open points, and source evidence.
