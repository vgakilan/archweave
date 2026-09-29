import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from openai import APIError
import pytest
from pydantic import ValidationError

from diagram_generator.analyzer_contract import RequirementAnalyzer
from diagram_generator.loader import load_diagram, save_diagram
from diagram_generator.openai_analyzer import (
    AnalyzerAPIError,
    AnalyzerRefusalError,
    AnalyzerValidationError,
    EmptyAnalyzerResponseError,
    InsufficientRequirementError,
    MissingAPIKeyError,
    OpenAIRequirementAnalyzer,
    StructuredAnalysis,
    StructuredGroup,
    StructuredNode,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MODEL = ROOT / "diagrams" / "model" / "sample.json"
PROMPT = ROOT / "prompts" / "requirement_analyzer.md"


def _parsed_sample() -> StructuredAnalysis:
    data = json.loads(SAMPLE_MODEL.read_text(encoding="utf-8"))
    data["groups"] = []
    for node in data["nodes"]:
        node.setdefault("group", None)
        node.setdefault("icon", None)
    for edge in data["edges"]:
        edge.setdefault("label", None)
        edge.setdefault("protocol", None)
    return StructuredAnalysis.model_validate(
        {"diagram": data, "insufficient_reason": None}
    )


def _client_with_response(parsed: StructuredAnalysis | None) -> Mock:
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(
        output=[], output_parsed=parsed, status="completed"
    )
    return client


def test_structured_output_supports_message_broker_type() -> None:
    node = StructuredNode(
        id="message_broker", label="Message Broker", type="message_broker", group=None,
        icon=None,
    )

    assert node.type == "message_broker"


def test_analyzer_uses_responses_parse_and_returns_domain_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    client = _client_with_response(_parsed_sample())
    analyzer = OpenAIRequirementAnalyzer(client=client)

    diagram = analyzer.analyze("Sample requirement")

    assert isinstance(analyzer, RequirementAnalyzer)
    assert diagram == load_diagram(SAMPLE_MODEL)
    client.responses.parse.assert_called_once_with(
        model="gpt-4.1-mini",
        instructions=PROMPT.read_text(encoding="utf-8"),
        input="Sample requirement",
        text_format=StructuredAnalysis,
        store=False,
    )
    generated = tmp_path / "sample.generated.json"
    save_diagram(diagram, generated)
    assert load_diagram(generated) == diagram
    assert "label" not in json.loads(generated.read_text(encoding="utf-8"))["edges"][0]


def test_analyzer_converts_structured_groups() -> None:
    parsed = _parsed_sample()
    assert parsed.diagram is not None
    parsed.diagram.groups = [
        StructuredGroup(id="users", label="Users", parent_group=None)
    ]
    parsed.diagram.nodes[0].group = "users"
    parsed.diagram.nodes[0].icon = "generic"

    diagram = OpenAIRequirementAnalyzer(client=_client_with_response(parsed)).analyze(
        "Sample requirement"
    )

    assert diagram.groups[0].id == "users"
    assert diagram.nodes[0].group == "users"
    assert diagram.nodes[0].icon == "generic"


def test_model_can_come_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "chosen-model")
    client = _client_with_response(_parsed_sample())

    OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")

    assert client.responses.parse.call_args.kwargs["model"] == "chosen-model"


def test_missing_api_key_fails_before_client_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        OpenAIRequirementAnalyzer()


def test_refusal_is_reported() -> None:
    client = _client_with_response(None)
    client.responses.parse.return_value.output = [
        SimpleNamespace(
            type="message",
            content=[SimpleNamespace(type="refusal", refusal="Request refused")],
        )
    ]

    with pytest.raises(AnalyzerRefusalError, match="Request refused"):
        OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")


def test_empty_parsed_response_is_reported() -> None:
    client = _client_with_response(None)

    with pytest.raises(EmptyAnalyzerResponseError, match="no parsed diagram"):
        OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")


def test_insufficient_requirement_is_reported() -> None:
    parsed = StructuredAnalysis(diagram=None, insufficient_reason="No components stated")
    client = _client_with_response(parsed)

    with pytest.raises(InsufficientRequirementError, match="No components stated"):
        OpenAIRequirementAnalyzer(client=client).analyze("Vague request")


def test_api_failure_is_reported() -> None:
    client = Mock()
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    client.responses.parse.side_effect = APIError("service unavailable", request, body=None)

    with pytest.raises(AnalyzerAPIError, match="service unavailable"):
        OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")


def test_structured_output_validation_failure_is_reported() -> None:
    client = Mock()
    with pytest.raises(ValidationError) as error:
        StructuredAnalysis.model_validate(
            {"diagram": {"diagram_type": "unsupported"}, "insufficient_reason": None}
        )
    client.responses.parse.side_effect = error.value

    with pytest.raises(AnalyzerValidationError, match="structured output"):
        OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")


def test_domain_validation_failure_is_reported() -> None:
    parsed = _parsed_sample()
    assert parsed.diagram is not None
    parsed.diagram.edges[0].target = "missing_node"
    client = _client_with_response(parsed)

    with pytest.raises(AnalyzerValidationError, match="unknown node ID"):
        OpenAIRequirementAnalyzer(client=client).analyze("Sample requirement")
