import json
from pathlib import Path

import pytest

from diagram_generator.loader import load_diagram, save_diagram
from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Diagram, Edge, Group, Node


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "diagrams" / "model" / "sample.json"
HMS = ROOT / "diagrams" / "model" / "hms.generated.json"


def _model_file(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "model.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _sample_data() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_ungrouped_model_keeps_legacy_json_and_mermaid(tmp_path: Path) -> None:
    diagram = load_diagram(SAMPLE)
    output = save_diagram(diagram, tmp_path / "saved.json")
    data = json.loads(output.read_text(encoding="utf-8"))

    assert diagram.groups == ()
    assert "groups" not in data
    assert all("group" not in node for node in data["nodes"])
    assert generate_mermaid(diagram) == (ROOT / "diagrams/source/sample.mmd").read_text(
        encoding="utf-8"
    )


def test_hms_groups_round_trip_and_subgraphs(tmp_path: Path) -> None:
    diagram = load_diagram(HMS)
    output = save_diagram(diagram, tmp_path / "hms.json")
    mermaid = generate_mermaid(diagram)

    assert load_diagram(output) == diagram
    assert [group.id for group in diagram.groups] == [
        "hospital_management_system",
        "presentation_layer",
        "application_layer",
        "data_layer",
    ]
    assert '    subgraph hospital_management_system["Hospital Management System"]' in mermaid
    assert "        direction LR" in mermaid
    assert '        subgraph application_layer["Application Layer"]' in mermaid
    assert '            authentication_module["Authentication Module"]' in mermaid
    assert '            notification_service["Notification Service"]' in mermaid
    assert '    patient(["Patient"])' in mermaid
    assert "    class hospital_management_system group_boundary;" in mermaid
    assert "    class application_layer group_nested;" in mermaid
    assert "    patient_portal -->|HTTPS| hms_backend" in mermaid
    assert not any(
        edge.source == "authentication_module" or edge.target == "authentication_module"
        for edge in diagram.edges
    )


def test_duplicate_and_conflicting_group_ids_fail() -> None:
    nodes = (Node("n", "Node", "application"),)
    with pytest.raises(ValueError, match="Duplicate group ID"):
        Diagram("D", "architecture", "LR", nodes, (), (Group("g", "G"), Group("g", "G")))
    with pytest.raises(ValueError, match="conflicts with a node ID"):
        Diagram("D", "architecture", "LR", nodes, (), (Group("n", "N"),))


def test_unknown_group_membership_and_parent_fail(tmp_path: Path) -> None:
    data = _sample_data()
    data["nodes"][0]["group"] = "missing"
    with pytest.raises(ValueError, match=r"nodes\[0\].group references unknown group ID"):
        load_diagram(_model_file(tmp_path, data))

    data = _sample_data()
    data["groups"] = [{"id": "child", "label": "Child", "parent_group": "missing"}]
    with pytest.raises(ValueError, match="parent_group references unknown group ID"):
        load_diagram(_model_file(tmp_path, data))


def test_deeper_nesting_fails(tmp_path: Path) -> None:
    data = _sample_data()
    data["groups"] = [
        {"id": "root", "label": "Root"},
        {"id": "child", "label": "Child", "parent_group": "root"},
        {"id": "grandchild", "label": "Grandchild", "parent_group": "child"},
    ]
    with pytest.raises(ValueError, match="exceeds one level of nesting"):
        load_diagram(_model_file(tmp_path, data))


def test_edges_still_reference_nodes_with_groups() -> None:
    with pytest.raises(ValueError, match="target references unknown node ID"):
        Diagram(
            "D",
            "architecture",
            "LR",
            (Node("n", "Node", "application", group="g"),),
            (Edge("n", "g"),),
            (Group("g", "Group"),),
        )
