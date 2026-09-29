"""Generate Mermaid and SVG artifacts from a validated diagram model."""

from pathlib import Path
import re

from diagram_generator.loader import load_diagram
from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Diagram
from diagram_generator.renderer import render_mermaid


def output_paths(
    model_path: str | Path, *, project_root: str | Path | None = None
) -> tuple[Path, Path]:
    """Derive artifact paths from a model filename, preserving dotted stems."""
    model = Path(model_path)
    if model.suffix.lower() != ".json":
        raise ValueError(f"Diagram model must be a .json file: {model}")
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    return (
        root / "diagrams" / "source" / f"{model.stem}.mmd",
        root / "diagrams" / "rendered" / f"{model.stem}.svg",
    )


def generate_diagram(
    model_path: str | Path, *, project_root: str | Path | None = None
) -> tuple[Path, Path]:
    """Validate a JSON model, write Mermaid, render SVG, and return both paths."""
    model = Path(model_path).resolve()
    output_paths(model, project_root=project_root)
    if not model.is_file():
        raise FileNotFoundError(f"Diagram model file not found: {model}")

    diagram = load_diagram(model)
    return generate_diagram_model(diagram, model.stem, project_root=project_root)


def generate_diagram_model(
    diagram: Diagram, output_stem: str, *, project_root: str | Path | None = None
) -> tuple[Path, Path]:
    """Write and render a validated in-memory diagram under diagrams/."""
    if (
        not output_stem
        or output_stem in {".", ".."}
        or re.search(r'[<>:"/\\|?*]', output_stem) is not None
    ):
        raise ValueError(f"Invalid output stem: {output_stem!r}")
    source, rendered = output_paths(f"{output_stem}.json", project_root=project_root)
    mermaid = generate_mermaid(diagram)
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(mermaid, encoding="utf-8", newline="\n")
    render_mermaid(source, rendered, project_root=project_root)
    return source, rendered


def generate_planned_views(
    model_path: str | Path,
    plan_path: str | Path,
    *,
    project_root: str | Path | None = None,
) -> tuple[tuple[str, Path, Path], ...]:
    """Validate a source model and plan, then render each selected view."""
    from diagram_generator.planner import load_diagram_plan, project_view

    diagram = load_diagram(model_path)
    plan = load_diagram_plan(plan_path)
    # Validate every view before writing or rendering any artifact.
    views = tuple((view.name, project_view(diagram, view)) for view in plan.views)
    return tuple(
        (name, *generate_diagram_model(view_diagram, name, project_root=project_root))
        for name, view_diagram in views
    )
