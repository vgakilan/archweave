"""Select evidence-backed requirement views and render a review package."""

from html import escape
import json
from pathlib import Path
import re
from xml.etree import ElementTree

from diagram_generator.mermaid import generate_architecture
from diagram_generator.renderer import render_mermaid
from diagram_generator.requirement_model import load_requirement_model


_ROOT = Path(__file__).resolve().parents[2]
_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_TYPES = {"architecture", "flowchart", "sequence"}
_DIRECTIONS = {"LR", "RL", "TB", "BT"}


def _label(value: str) -> str:
    return escape(value, quote=True).replace("|", "#124;")


def _load_plan(path: str | Path, model: dict) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"views"} or not isinstance(data["views"], list) or not data["views"]:
        raise ValueError("Review plan must contain a nonempty views array")
    names: set[str] = set()
    nodes = {x["id"]: x for x in model["nodes"]}
    edges = {x["id"]: x for x in model["edges"]}
    processes = {x["id"]: x for x in model["processes"]}
    for view in data["views"]:
        if not isinstance(view, dict) or set(view) != {"name", "title", "purpose", "type", "scope", "fact_ids", "direction"}:
            raise ValueError("Each view needs name, title, purpose, type, scope, fact_ids, and direction")
        name = view["name"]
        if not isinstance(name, str) or not _ID.fullmatch(name) or name in names:
            raise ValueError(f"Invalid or duplicate view name: {name!r}")
        names.add(name)
        if any(not isinstance(view[key], str) or not view[key].strip() for key in ("title", "purpose")):
            raise ValueError(f"View {name} needs a title and purpose")
        if view["type"] not in _TYPES or view["scope"] not in {"current", "future"} or view["direction"] not in _DIRECTIONS:
            raise ValueError(f"View {name} has an unsupported type, scope, or direction")
        ids = view["fact_ids"]
        if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"View {name} needs unique fact IDs")
        allowed = (set(nodes) | set(edges)) if view["type"] == "architecture" else set(processes) if view["type"] == "flowchart" else set(edges)
        if set(ids) - allowed:
            raise ValueError(f"View {name} selects facts unsupported by {view['type']}")
        facts = [nodes.get(x) or edges.get(x) or processes.get(x) for x in ids]
        if any(fact["scope"] != view["scope"] for fact in facts):
            raise ValueError(f"View {name} mixes current and future facts")
        if view["type"] == "architecture":
            selected_nodes = set(ids) & set(nodes)
            if not selected_nodes:
                raise ValueError(f"Architecture view {name} needs a node")
            for fact in facts:
                if fact["id"] in edges and (fact["source"] not in selected_nodes or fact["target"] not in selected_nodes):
                    raise ValueError(f"View {name} omits an edge endpoint")
        elif view["type"] == "flowchart" and len(ids) != 1:
            raise ValueError(f"Flowchart view {name} must select one process")
        elif view["type"] == "sequence":
            if len(ids) < 2 or any("sequence" not in fact for fact in facts):
                raise ValueError(f"Sequence view {name} needs ordered edges")
            if len({fact["scenario"] for fact in facts}) != 1 or len({fact["sequence"] for fact in facts}) != len(facts):
                raise ValueError(f"Sequence view {name} needs one scenario with unique message positions")
            participants = {fact["source"] for fact in facts} | {fact["target"] for fact in facts}
            if any(nodes[p]["scope"] != view["scope"] for p in participants):
                raise ValueError(f"Sequence view {name} mixes current and future participants")
    return data["views"]


def _mermaid(view: dict, model: dict) -> str:
    nodes = {x["id"]: x for x in model["nodes"]}
    edges = {x["id"]: x for x in model["edges"]}
    if view["type"] == "architecture":
        return generate_architecture(
            [nodes[x] for x in view["fact_ids"] if x in nodes],
            [edges[x] for x in view["fact_ids"] if x in edges],
            view["direction"],
        )
    if view["type"] == "flowchart":
        process = next(x for x in model["processes"] if x["id"] == view["fact_ids"][0])
        lines = [f"flowchart {view['direction']}"]
        for step in process["steps"]:
            label = _label(step["name"])
            shape = f'{{"{label}"}}' if step["kind"] == "decision" else f'(["{label}"])' if step["kind"] == "outcome" else f'["{label}"]'
            lines.append(f"    {step['id']}{shape}")
        for transition in process["transitions"]:
            label = transition.get("condition")
            arrow = f"-->|{_label(label)}|" if label else "-->"
            lines.append(f"    {transition['source']} {arrow} {transition['target']}")
        return "\n".join(lines) + "\n"
    messages = sorted((edges[x] for x in view["fact_ids"]), key=lambda x: x["sequence"])
    participants = list(dict.fromkeys(p for m in messages for p in (m["source"], m["target"])))
    lines = ["sequenceDiagram"]
    lines.extend(f'    participant {p} as {_label(nodes[p]["name"])}' for p in participants)
    lines.extend(f'    {m["source"]}->>{m["target"]}: {_label(m["action"])}' for m in messages)
    return "\n".join(lines) + "\n"


def _report(model: dict, views: list[dict]) -> str:
    lines = [f"# {model['title']}", "", f"Source: `{model['source_markdown']}`", ""]
    names = {node["id"]: node["name"] for node in model["nodes"]}
    if model["nodes"]:
        lines.extend(["## Named participants and components", ""])
        for node in model["nodes"]:
            lines.append(f"- [{node['scope']}] {node['name']} ({node['type'].replace('_', ' ')})")
        lines.append("")
    if model["edges"]:
        lines.extend(["## Stated connections", ""])
        for edge in model["edges"]:
            protocol = f" ({edge['protocol']})" if edge.get("protocol") else ""
            lines.append(
                f"- [{edge['scope']}] {names[edge['source']]} → "
                f"{names[edge['target']]}: {edge['action'].rstrip('. ')}{protocol}."
            )
        lines.append("")
    if model["processes"]:
        lines.extend(["## Stated processes", ""])
        for process in model["processes"]:
            lines.append(f"### {process['name']} ({process['scope']})")
            lines.append("")
            steps = {step["id"]: step["name"] for step in process["steps"]}
            if process["transitions"]:
                for transition in process["transitions"]:
                    condition = f" when {transition['condition'].rstrip('. ')}" if transition.get("condition") else ""
                    lines.append(
                        f"- {steps[transition['source']]} → {steps[transition['target']]}{condition}."
                    )
            else:
                lines.extend(f"- {step['name']}" for step in process["steps"])
            lines.append("")
    if model["statements"]:
        lines.extend(["## Other stated requirements", ""])
        for statement in model["statements"]:
            lines.append(f"- [{statement['scope']}] {statement['text']}")
        lines.append("")
    lines.extend(["## Views", ""])
    covered = set()
    for view in views:
        covered.update(view["fact_ids"])
        lines.append(f"- **{view['title']}** ({view['type']}, {view['scope']}): {view['purpose']} [SVG](../rendered/{view['name']}.svg)")
    remaining = [x for key in ("nodes", "edges", "processes") for x in model[key] if x["id"] not in covered]
    if remaining:
        lines.extend(["", "## Facts outside the views", ""])
        for fact in remaining:
            content = fact.get("text") or fact.get("name") or fact.get("action")
            lines.append(f"- [{fact['scope']}] {content} — {fact['evidence']['section']} (`{fact['id']}`)")
    if model["open_points"]:
        lines.extend(["", "## Open points", ""])
        for point in model["open_points"]:
            lines.append(f"- {point['question']} — {point['evidence']['section']} (`{point['id']}`)")
    lines.extend(["", "## Evidence index", ""])
    for key in ("nodes", "edges", "processes", "statements", "open_points"):
        for fact in model[key]:
            lines.append(f"- `{fact['id']}` — {fact['evidence']['section']}: “{fact['evidence']['excerpt']}”")
            if key == "processes":
                for child in (*fact["steps"], *fact["transitions"]):
                    lines.append(f"- `{child['id']}` — {child['evidence']['section']}: “{child['evidence']['excerpt']}”")
    return "\n".join(lines) + "\n"


def generate_review_package(model_path: str | Path, plan_path: str | Path, *, project_root: str | Path | None = None) -> tuple[Path, ...]:
    """Validate all selections, then render SVG views and a Markdown companion."""
    model = load_requirement_model(model_path)
    views = _load_plan(plan_path, model)
    sources = [(view, _mermaid(view, model)) for view in views]
    root = Path(project_root) if project_root is not None else _ROOT
    written: list[Path] = []
    for view, mermaid in sources:
        source = root / "diagrams" / "source" / f"{view['name']}.mmd"
        svg = root / "diagrams" / "rendered" / f"{view['name']}.svg"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(mermaid, encoding="utf-8")
        render_mermaid(source, svg, project_root=_ROOT)
        ElementTree.parse(svg)
        written.extend((source, svg))
    report = root / "diagrams" / "reports" / f"{Path(model_path).stem}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_report(model, views), encoding="utf-8")
    written.append(report)
    return tuple(written)
