import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from diagram_generator.loader import load_diagram
from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Edge, Node


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "diagrams" / "model" / "sample.json"
SOURCE = ROOT / "diagrams" / "source" / "sample.mmd"
SCHEMA = ROOT / "schemas" / "diagram.schema.json"


def _write_model(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "diagram.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _sample_data() -> dict:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def test_load_sample_model() -> None:
    diagram = load_diagram(MODEL)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert Draft202012Validator(schema).is_valid(_sample_data())
    assert diagram.title == "Online Shopping Architecture"
    assert diagram.diagram_type == "architecture"
    assert diagram.direction == "LR"
    assert diagram.nodes == (
        Node("customer", "Customer", "actor"),
        Node("web_application", "Web Application", "application"),
        Node("api_gateway", "API Gateway", "gateway"),
        Node("order_service", "Order Service", "service"),
        Node("payment_service", "Payment Service", "service"),
        Node("postgresql", "PostgreSQL", "database"),
        Node("external_payment_provider", "External Payment Provider", "external_system"),
    )
    assert diagram.edges == (
        Edge("customer", "web_application"),
        Edge("web_application", "api_gateway"),
        Edge("api_gateway", "order_service", label="Order requests"),
        Edge("api_gateway", "payment_service", label="Payment requests"),
        Edge("order_service", "postgresql", label="Stores order information"),
        Edge("payment_service", "external_payment_provider", protocol="HTTPS"),
    )


def test_mermaid_matches_sample_source() -> None:
    generated = generate_mermaid(load_diagram(MODEL))

    assert generated == SOURCE.read_text(encoding="utf-8")
    assert generated.startswith("flowchart LR\n")
    assert "web_application --> api_gateway" in generated
    assert "web_application -->|HTTPS| api_gateway" not in generated
    assert "api_gateway -->|Order requests| order_service" in generated
    assert "api_gateway -->|Payment requests| payment_service" in generated
    assert "order_service -->|Stores order information| postgresql" in generated
    assert "payment_service -->|HTTPS| external_payment_provider" in generated


def test_loader_rejects_duplicate_node_id(tmp_path: Path) -> None:
    data = _sample_data()
    data["nodes"][1]["id"] = "customer"

    with pytest.raises(ValueError, match="Duplicate node ID 'customer'"):
        load_diagram(_write_model(tmp_path, data))


def test_loader_rejects_empty_node_id(tmp_path: Path) -> None:
    data = _sample_data()
    data["nodes"][0]["id"] = ""

    with pytest.raises(ValueError, match=r"nodes\[0\].id"):
        load_diagram(_write_model(tmp_path, data))


def test_loader_rejects_missing_edge_target(tmp_path: Path) -> None:
    data = _sample_data()
    del data["edges"][0]["target"]

    with pytest.raises(ValueError, match=r"edges\[0\].*'target' is a required property"):
        load_diagram(_write_model(tmp_path, data))


def test_loader_rejects_unknown_node_reference(tmp_path: Path) -> None:
    data = _sample_data()
    data["edges"][0]["target"] = "missing_node"

    with pytest.raises(ValueError, match=r"edges\[0\].target references unknown node ID"):
        load_diagram(_write_model(tmp_path, data))


def test_loader_rejects_unsupported_node_type(tmp_path: Path) -> None:
    data = _sample_data()
    data["nodes"][0]["type"] = "queue"

    with pytest.raises(ValueError, match=r"nodes\[0\].type.*'queue' is not one of"):
        load_diagram(_write_model(tmp_path, data))


def test_loader_rejects_unsupported_diagram_type(tmp_path: Path) -> None:
    data = _sample_data()
    data["diagram_type"] = "sequence"

    with pytest.raises(ValueError, match=r"diagram_type.*'sequence' is not one of"):
        load_diagram(_write_model(tmp_path, data))


@pytest.mark.parametrize("value", ["", "   "])
def test_loader_rejects_empty_node_label(tmp_path: Path, value: str) -> None:
    data = _sample_data()
    data["nodes"][0]["label"] = value

    with pytest.raises(ValueError, match=r"nodes\[0\].label"):
        load_diagram(_write_model(tmp_path, data))
