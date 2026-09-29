from diagram_generator.mermaid import generate_mermaid
from diagram_generator.models import Diagram, Node


def test_every_node_type_receives_a_shared_class_and_shape() -> None:
    node_types = (
        "actor",
        "application",
        "service",
        "gateway",
        "database",
        "external_system",
        "message_broker",
    )
    diagram = Diagram(
        title="Types",
        diagram_type="architecture",
        direction="LR",
        nodes=tuple(Node(f"n_{kind}", kind, kind) for kind in node_types),
        edges=(),
    )

    source = generate_mermaid(diagram)

    for kind in node_types:
        assert f"    classDef type_{kind} " in source
        assert f"    class n_{kind} type_{kind};" in source
    assert 'n_actor(["actor"])' in source
    assert 'n_application("application")' in source
    assert 'n_service["service"]' in source
    assert 'n_gateway{"gateway"}' in source
    assert 'n_database[("database")]' in source
    assert 'n_external_system[["external_system"]]' in source
    assert 'n_message_broker{{"message_broker"}}' in source
