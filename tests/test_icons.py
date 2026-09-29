import json
from pathlib import Path
from unittest.mock import patch

import pytest

from diagram_generator.icons import GENERIC_ICONS, resolve_icon
from diagram_generator.loader import load_diagram, save_diagram
from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Diagram, Node


ROOT = Path(__file__).resolve().parents[1]
ORDER_MODEL = ROOT / "diagrams/model/order_processing.generated.json"


def test_icon_metadata_round_trips_without_changing_architecture(tmp_path: Path) -> None:
    original = json.loads(ORDER_MODEL.read_text(encoding="utf-8"))
    plain = json.loads(ORDER_MODEL.read_text(encoding="utf-8"))
    for node in plain["nodes"]:
        node.pop("icon")
    plain_path = tmp_path / "plain.json"
    plain_path.write_text(json.dumps(plain), encoding="utf-8")

    with_icons = load_diagram(ORDER_MODEL)
    without_icons = load_diagram(plain_path)
    saved = save_diagram(with_icons, tmp_path / "saved.json")

    assert json.loads(saved.read_text(encoding="utf-8")) == original
    assert with_icons.edges == without_icons.edges
    assert with_icons.groups == without_icons.groups
    assert [(n.id, n.label, n.type, n.group) for n in with_icons.nodes] == [
        (n.id, n.label, n.type, n.group) for n in without_icons.nodes
    ]
    assert all(node.icon is None for node in without_icons.nodes)


def test_generic_mapping_covers_every_node_type() -> None:
    assert set(GENERIC_ICONS) == {
        "actor", "application", "service", "gateway", "database",
        "external_system", "message_broker",
    }


def test_unknown_icon_falls_back_to_generic_then_plain_shape() -> None:
    node = Node("customer", "Customer", "actor", icon="unavailable:brand")
    diagram = Diagram("D", "architecture", "LR", (node,), ())

    with patch("diagram_generator.icons._available_icons", return_value={"user-round"}):
        assert 'icon: "lucide:user-round"' in generate_mermaid(diagram)

    with patch("diagram_generator.icons._available_icons", return_value=set()):
        assert 'customer(["Customer"])' in generate_mermaid(diagram)
        assert "shape: icon" not in generate_mermaid(diagram)


def test_explicit_technology_icon_uses_local_pack_when_available() -> None:
    with patch("diagram_generator.icons._available_icons", return_value={"postgresql"}):
        assert resolve_icon("database", "simple-icons:postgresql") == "simple-icons:postgresql"


def test_empty_icon_is_invalid_metadata(tmp_path: Path) -> None:
    data = json.loads(ORDER_MODEL.read_text(encoding="utf-8"))
    data["nodes"][0]["icon"] = ""
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match=r"nodes\[0\].icon"):
        load_diagram(path)
