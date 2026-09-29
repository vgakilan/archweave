"""Load and validate structured diagrams from JSON files."""

from dataclasses import asdict
from functools import lru_cache
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from diagram_generator.models import Diagram, Edge, Group, Node


_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "diagram.schema.json"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _error_location(parts: list[str | int]) -> str:
    location = "$"
    for part in parts:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    return location


def load_diagram(path: str | Path) -> Diagram:
    """Validate JSON against the schema, then build the structured model."""
    source = Path(path)
    with source.open(encoding="utf-8") as file:
        data = json.load(file)

    errors = sorted(
        _validator().iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise ValueError(
            f"Invalid diagram model {source} at "
            f"{_error_location(list(error.absolute_path))}: {error.message}"
        )

    try:
        groups = tuple(
            Group(
                id=item["id"],
                label=item["label"],
                parent_group=item.get("parent_group"),
            )
            for item in data.get("groups", [])
        )
        nodes = tuple(
            Node(
                id=item["id"],
                label=item["label"],
                type=item["type"],
                group=item.get("group"),
                icon=item.get("icon"),
            )
            for item in data["nodes"]
        )
        edges = tuple(
            Edge(
                source=item["source"],
                target=item["target"],
                label=item.get("label"),
                protocol=item.get("protocol"),
            )
            for item in data["edges"]
        )
        return Diagram(
            title=data["title"],
            diagram_type=data["diagram_type"],
            direction=data["direction"],
            nodes=nodes,
            edges=edges,
            groups=groups,
        )
    except ValueError as exc:
        raise ValueError(f"Invalid diagram model {source}: {exc}") from exc


def save_diagram(diagram: Diagram, path: str | Path) -> Path:
    """Write a domain Diagram as JSON matching the diagram schema."""
    data = {
        "title": diagram.title,
        "diagram_type": diagram.diagram_type,
        "direction": diagram.direction,
        "nodes": [
            {key: value for key, value in asdict(node).items() if value is not None}
            for node in diagram.nodes
        ],
        "edges": [
            {key: value for key, value in asdict(edge).items() if value is not None}
            for edge in diagram.edges
        ],
    }
    if diagram.groups:
        data["groups"] = [
            {key: value for key, value in asdict(group).items() if value is not None}
            for group in diagram.groups
        ]
    error = next(_validator().iter_errors(data), None)
    if error is not None:
        raise ValueError(f"Diagram does not match JSON schema: {error.message}")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
