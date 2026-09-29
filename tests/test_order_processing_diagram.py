from pathlib import Path

from diagram_generator.loader import load_diagram
from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Edge, Node


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "diagrams" / "model" / "order_processing.generated.json"
SOURCE = ROOT / "diagrams" / "source" / "order_processing.mmd"


def test_order_processing_uses_only_stated_architecture() -> None:
    diagram = load_diagram(MODEL)

    assert Node("relational_database", "Relational Database", "database", icon="generic") in diagram.nodes
    assert Node("message_broker", "Message Broker", "message_broker", icon="generic") in diagram.nodes
    assert Node("order_api", "Order API", "service", icon="generic") in diagram.nodes
    assert all(node.icon == "generic" for node in diagram.nodes)
    assert all(edge.protocol is None for edge in diagram.edges)
    assert Edge(
        "order_processing_service", "message_broker", label="Publishes OrderCreated event"
    ) in diagram.edges
    assert Edge("message_broker", "inventory_service", label="OrderCreated event") in diagram.edges
    assert Edge("inventory_service", "external_warehouse_system") in diagram.edges


def test_order_processing_mermaid_matches_validated_model() -> None:
    diagram = load_diagram(MODEL)

    generated = generate_mermaid(diagram)
    assert SOURCE.read_text(encoding="utf-8") == generated
    assert 'message_broker@{ shape: icon, icon: "lucide:messages-square"' in generated
    assert 'relational_database@{ shape: icon, icon: "lucide:database"' in generated
    assert "simple-icons:" not in generated
    assert "    class message_broker type_message_broker;" in generated
