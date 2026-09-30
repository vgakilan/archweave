"""Evidence-backed requirement facts, independent of diagram notation."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator


_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "requirement.schema.json"
_ROOT = Path(__file__).resolve().parents[2]


def load_requirement_model(path: str | Path) -> dict:
    """Load a requirement model and validate its references and process paths."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: str(e.path))
    if errors:
        error = errors[0]
        raise ValueError(f"Invalid requirement model at {list(error.path)}: {error.message}")

    markdown_path = Path(data["source_markdown"])
    if not markdown_path.is_absolute():
        markdown_path = _ROOT / markdown_path
    markdown = markdown_path.read_text(encoding="utf-8")
    if not markdown.strip():
        raise ValueError("Parsed Markdown is empty")

    all_ids: set[str] = set()
    def register(item: dict) -> None:
        if item["id"] in all_ids:
            raise ValueError(f"Duplicate fact ID: {item['id']}")
        all_ids.add(item["id"])

    for collection in ("nodes", "edges", "processes", "statements", "open_points"):
        for item in data[collection]:
            register(item)
            if item["evidence"]["excerpt"] not in markdown:
                raise ValueError(f"Evidence for {item['id']} is absent from parsed Markdown")
            if collection == "processes":
                for step in item["steps"]:
                    register(step)
                    if step["evidence"]["excerpt"] not in markdown:
                        raise ValueError(f"Evidence for {step['id']} is absent from parsed Markdown")
                for transition in item["transitions"]:
                    register(transition)
                    if transition["evidence"]["excerpt"] not in markdown:
                        raise ValueError(f"Evidence for {transition['id']} is absent from parsed Markdown")

    if not data["nodes"] and not data["processes"]:
        raise ValueError("Requirement has no supported nodes or process")

    nodes = {item["id"] for item in data["nodes"]}
    positions: set[tuple[str, int]] = set()
    for edge in data["edges"]:
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise ValueError(f"Edge {edge['id']} references an unknown node")
        if "scenario" in edge:
            position = (edge["scenario"], edge["sequence"])
            if position in positions:
                raise ValueError(f"Duplicate sequence position in {edge['scenario']}")
            positions.add(position)
    for process in data["processes"]:
        steps = {step["id"] for step in process["steps"]}
        if not steps:
            raise ValueError(f"Process {process['id']} has no steps")
        for step in process["steps"]:
            if step.get("performed_by") and step["performed_by"] not in nodes:
                raise ValueError(f"Step {step['id']} references an unknown node")
        for transition in process["transitions"]:
            if transition["source"] not in steps or transition["target"] not in steps:
                raise ValueError(f"Transition {transition['id']} references an unknown step")
            if transition["source"] == transition["target"]:
                raise ValueError(f"Transition {transition['id']} loops to the same step")
    return data
