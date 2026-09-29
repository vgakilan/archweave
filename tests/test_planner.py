from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from diagram_generator.loader import load_diagram
from diagram_generator.models import Edge
from diagram_generator.pipeline import generate_planned_views
from diagram_generator.planner import load_diagram_plan, project_view


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "diagrams/model/banking_system_requirement.generated.json"
PLAN = ROOT / "diagrams/plans/banking_system_requirement.json"


def test_banking_views_only_filter_source_facts() -> None:
    source = load_diagram(MODEL)
    plans = load_diagram_plan(PLAN).views

    assert [plan.name for plan in plans] == [
        "banking_context", "banking_services", "banking_infrastructure",
        "banking_messaging"
    ]
    assert [(len(plan.included_node_ids), len(plan.included_edges)) for plan in plans] == [
        (3, 0), (6, 0), (3, 0), (3, 2)
    ]
    for plan in plans:
        view = project_view(source, plan)
        source_by_id = {node.id: node for node in source.nodes}
        assert [replace(node, group=None) for node in view.nodes] == [
            replace(source_by_id[node_id], group=None)
            for node_id in plan.included_node_ids
        ]
        assert set(view.edges).issubset(set(source.edges))
        assert view.direction == "LR"
        assert all(edge.source in {node.id for node in view.nodes} for edge in view.edges)
        assert all(edge.target in {node.id for node in view.nodes} for edge in view.edges)

    messaging = project_view(source, plans[3])
    assert [(edge.source, edge.target) for edge in messaging.edges] == [
        ("transaction_service", "kafka"),
        ("kafka", "fraud_detection_service"),
    ]
    assert load_diagram(MODEL) == source


def test_planner_rejects_unknown_nodes_and_invented_edges() -> None:
    source = load_diagram(MODEL)
    view = load_diagram_plan(PLAN).views[3]

    with pytest.raises(ValueError, match="unknown nodes"):
        project_view(source, replace(view, included_node_ids=("missing",)))
    with pytest.raises(ValueError, match="absent from the source"):
        project_view(
            source,
            replace(view, included_edges=(Edge("transaction_service", "fraud_detection_service"),)),
        )
    with pytest.raises(ValueError, match="outside its included nodes"):
        project_view(source, replace(view, included_node_ids=("transaction_service", "kafka")))


def test_planner_enforces_flow_group_and_size_constraints() -> None:
    source = load_diagram(MODEL)
    context, services, _, messaging = load_diagram_plan(PLAN).views

    with pytest.raises(ValueError, match="recommended node maximum"):
        project_view(source, replace(services, max_recommended_nodes=5))
    with pytest.raises(ValueError, match="unstated relationship"):
        project_view(source, replace(messaging, primary_flow=("fraud_detection_service", "kafka")))
    with pytest.raises(ValueError, match="outside its boundary group"):
        project_view(source, replace(context, external_system_placement="banking_system_boundary"))


def test_planned_pipeline_renders_each_view(tmp_path: Path) -> None:
    def render(source: Path, output: Path, *, project_root: Path) -> Path:
        assert project_root == tmp_path
        assert source.is_file()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("<svg/>", encoding="utf-8")
        return output

    with patch("diagram_generator.pipeline.render_mermaid", side_effect=render) as mock:
        results = generate_planned_views(MODEL, PLAN, project_root=tmp_path)

    assert [name for name, _, _ in results] == [
        "banking_context", "banking_services", "banking_infrastructure",
        "banking_messaging"
    ]
    assert mock.call_count == 4
    for name, source, svg in results:
        assert source.name == f"{name}.mmd"
        assert svg.name == f"{name}.svg"
        assert svg.read_text(encoding="utf-8") == "<svg/>"
    assert (
        "transaction_service -->|Publishes event for fraud detection| kafka"
        in results[3][1].read_text(encoding="utf-8")
    )
