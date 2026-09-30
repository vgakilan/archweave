import json
from pathlib import Path
from unittest.mock import patch

import pytest

from diagram_generator.requirement_model import load_requirement_model
from diagram_generator.review_package import generate_review_package


def _input(tmp_path: Path) -> tuple[Path, Path]:
    markdown = tmp_path / "parsed.md"
    markdown.write_text(
        "# Order\nCustomer sends an order to Order Service.\n"
        "Order Service sends a payment request to Payment Service.\n"
        "If payment succeeds, confirm the order. If payment fails, reject the order.\n"
        "Payments must be idempotent.\n",
        encoding="utf-8",
    )
    def evidence(excerpt: str) -> dict:
        return {"section": "Order", "excerpt": excerpt}
    model = {
        "title": "Order", "source_markdown": str(markdown),
        "nodes": [
            {"id": "customer", "name": "Customer", "type": "actor", "scope": "current", "evidence": evidence("Customer")},
            {"id": "order_service", "name": "Order Service", "type": "service", "scope": "current", "evidence": evidence("Order Service")},
            {"id": "payment_service", "name": "Payment Service", "type": "service", "scope": "current", "evidence": evidence("Payment Service")},
        ],
        "edges": [
            {"id": "send_order", "source": "customer", "target": "order_service", "action": "sends an order", "scope": "current", "scenario": "order", "sequence": 1, "evidence": evidence("Customer sends an order to Order Service.")},
            {"id": "request_payment", "source": "order_service", "target": "payment_service", "action": "sends a payment request", "scope": "current", "scenario": "order", "sequence": 2, "evidence": evidence("Order Service sends a payment request to Payment Service.")},
        ],
        "processes": [{
            "id": "payment_result", "name": "Payment result", "scope": "current", "evidence": evidence("If payment succeeds"),
            "steps": [
                {"id": "payment_decision", "name": "Payment succeeds?", "kind": "decision", "evidence": evidence("If payment succeeds")},
                {"id": "confirm", "name": "Confirm the order", "kind": "outcome", "evidence": evidence("confirm the order")},
                {"id": "reject", "name": "Reject the order", "kind": "outcome", "evidence": evidence("reject the order")},
            ],
            "transitions": [
                {"id": "success", "source": "payment_decision", "target": "confirm", "condition": "payment succeeds", "evidence": evidence("If payment succeeds, confirm the order")},
                {"id": "failure", "source": "payment_decision", "target": "reject", "condition": "payment fails", "evidence": evidence("If payment fails, reject the order")},
            ],
        }],
        "statements": [{"id": "idempotency", "text": "Payments must be idempotent.", "scope": "current", "evidence": evidence("Payments must be idempotent.")}],
        "open_points": [],
    }
    plan = {"views": [
        {"name": "overview", "title": "Order overview", "purpose": "See participants and connections", "type": "architecture", "scope": "current", "fact_ids": ["customer", "order_service", "payment_service", "send_order", "request_payment"], "direction": "LR"},
        {"name": "payment_path", "title": "Payment result", "purpose": "See both outcomes", "type": "flowchart", "scope": "current", "fact_ids": ["payment_result"], "direction": "TB"},
        {"name": "order_messages", "title": "Order messages", "purpose": "See message order", "type": "sequence", "scope": "current", "fact_ids": ["request_payment", "send_order"], "direction": "LR"},
    ]}
    model_path, plan_path = tmp_path / "model.json", tmp_path / "plan.json"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return model_path, plan_path


def test_review_package_generates_three_distinct_views_and_companion(tmp_path: Path) -> None:
    model, plan = _input(tmp_path)
    def render(source: Path, output: Path, *, project_root: Path) -> Path:
        assert source.is_file()
        assert project_root == Path(__file__).resolve().parents[1]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("<svg/>", encoding="utf-8")
        return output

    with patch("diagram_generator.review_package.render_mermaid", side_effect=render):
        files = generate_review_package(model, plan, project_root=tmp_path)
    assert len(files) == 7
    assert all(path.is_file() and path.stat().st_size for path in files)
    overview = (tmp_path / "diagrams/source/overview.mmd").read_text(encoding="utf-8")
    assert 'customer -->|"sends an order"| order_service' in overview
    assert 'order_service -->|"sends a payment request"| payment_service' in overview
    assert "sequenceDiagram" in (tmp_path / "diagrams/source/order_messages.mmd").read_text(encoding="utf-8")
    assert "payment_decision -->|payment succeeds| confirm" in (tmp_path / "diagrams/source/payment_path.mmd").read_text(encoding="utf-8")
    report = files[-1].read_text(encoding="utf-8")
    assert "Customer → Order Service: sends an order." in report
    assert "Payment succeeds? → Confirm the order when payment succeeds." in report
    assert "Payments must be idempotent" in report
    assert "order_messages.svg" in report


def test_requirement_model_rejects_unsupported_evidence_and_references(tmp_path: Path) -> None:
    model_path, _ = _input(tmp_path)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["edges"][0]["evidence"]["excerpt"] = "Not present in Markdown"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    with pytest.raises(ValueError, match="absent from parsed Markdown"):
        load_requirement_model(model_path)
    model["edges"][0]["evidence"]["excerpt"] = "Customer sends an order to Order Service."
    model["edges"][0]["target"] = "unknown"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown node"):
        load_requirement_model(model_path)


def test_review_plan_rejects_invented_sequence_and_missing_endpoint(tmp_path: Path) -> None:
    model_path, plan_path = _input(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["views"][0]["fact_ids"].remove("customer")
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="omits an edge endpoint"):
        generate_review_package(model_path, plan_path, project_root=tmp_path)
    plan["views"][0]["fact_ids"].append("customer")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    del model["edges"][0]["sequence"]
    del model["edges"][0]["scenario"]
    model_path.write_text(json.dumps(model), encoding="utf-8")
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="needs ordered edges"):
        generate_review_package(model_path, plan_path, project_root=tmp_path)


def test_render_failure_prevents_companion_report(tmp_path: Path) -> None:
    model, plan = _input(tmp_path)
    with patch("diagram_generator.review_package.render_mermaid", side_effect=RuntimeError("render failed")):
        with pytest.raises(RuntimeError, match="render failed"):
            generate_review_package(model, plan, project_root=tmp_path)
    assert not (tmp_path / "diagrams/reports/model.md").exists()


def test_review_plan_rejects_mixed_current_and_future_facts(tmp_path: Path) -> None:
    model_path, plan_path = _input(tmp_path)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["nodes"][0]["scope"] = "future"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    with pytest.raises(ValueError, match="mixes current and future facts"):
        generate_review_package(model_path, plan_path, project_root=tmp_path)
