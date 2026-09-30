"""Orchestrate parsing, analysis, planning, and rendering."""

from collections.abc import Callable
import json
from pathlib import Path
import re

from diagram_generator.document_parser import parse_document
from diagram_generator.requirement_model import load_requirement_model
from diagram_generator.review_package import generate_review_package


_ROOT = Path(__file__).resolve().parents[2]
Extractor = Callable[[str], dict]
Planner = Callable[[dict], dict]


def _stem(path: Path) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_").lower()
    if not name:
        raise ValueError("Document name cannot form an output stem")
    return name


def run_workflow(
    document: str | Path,
    *,
    extract: Extractor,
    plan: Planner,
    project_root: str | Path | None = None,
) -> tuple[Path, ...]:
    """Run the full workflow with separately supplied interpretation functions."""
    root = Path(project_root) if project_root is not None else _ROOT
    source = Path(document).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Requirement document not found: {source}")
    markdown_path = (
        source
        if source.suffix.lower() == ".md"
        else parse_document(
            source, root / "requirements" / "parsed" / f"{source.name}.md"
        )
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    if not markdown.strip():
        raise ValueError("Parsed Markdown is empty")

    model = extract(markdown)
    if not isinstance(model, dict):
        raise ValueError("Analyzer must return a JSON object")
    model = {**model, "source_markdown": str(markdown_path)}
    name = _stem(source)
    model_path = root / "diagrams" / "model" / f"{name}.requirement.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validated = load_requirement_model(model_path)

    view_plan = plan(validated)
    if not isinstance(view_plan, dict):
        raise ValueError("Planner must return a JSON object")
    plan_path = root / "diagrams" / "plans" / f"{name}.review.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(view_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = generate_review_package(model_path, plan_path, project_root=root)
    return (markdown_path, model_path, plan_path, *artifacts)
