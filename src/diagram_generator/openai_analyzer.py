"""OpenAI Responses implementation of the RequirementAnalyzer contract."""

import os
from pathlib import Path
from typing import Literal

from openai import APIError, OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError

from diagram_generator.models import Diagram, Edge, Group, Node


DEFAULT_MODEL = "gpt-4.1-mini"
_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "requirement_analyzer.md"


class AnalyzerError(RuntimeError):
    """The analyzer could not return a validated diagram."""


class MissingAPIKeyError(AnalyzerError):
    """OPENAI_API_KEY is required for a real OpenAI client."""


class AnalyzerRefusalError(AnalyzerError):
    """The model refused the requirement."""


class EmptyAnalyzerResponseError(AnalyzerError):
    """The API returned no parsed structured output."""


class AnalyzerAPIError(AnalyzerError):
    """The Responses API request failed."""


class AnalyzerValidationError(AnalyzerError):
    """Structured output failed parsing or domain validation."""


class InsufficientRequirementError(AnalyzerError):
    """The requirement cannot support a valid diagram."""


class StructuredGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    label: str
    parent_group: str | None


class StructuredNode(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    label: str
    type: Literal[
        "actor",
        "application",
        "service",
        "gateway",
        "database",
        "message_broker",
        "external_system",
    ]
    group: str | None
    icon: str | None


class StructuredEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source: str
    target: str
    label: str | None
    protocol: str | None


class StructuredDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: str
    diagram_type: Literal["architecture", "flowchart"]
    direction: Literal["LR", "RL", "TB", "BT"]
    groups: list[StructuredGroup]
    nodes: list[StructuredNode]
    edges: list[StructuredEdge]


class StructuredAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    diagram: StructuredDiagram | None
    insufficient_reason: str | None


class OpenAIRequirementAnalyzer:
    """Extract a validated Diagram with the Responses API and Structured Outputs."""

    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        model: str | None = None,
        prompt_path: str | Path = _PROMPT_PATH,
    ) -> None:
        if client is None:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise MissingAPIKeyError("OPENAI_API_KEY is not set")
            client = OpenAI(api_key=api_key)

        self._client = client
        self._model = model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL
        self._instructions = Path(prompt_path).read_text(encoding="utf-8")

    def analyze(self, requirement_text: str) -> Diagram:
        if not isinstance(requirement_text, str) or not requirement_text.strip():
            raise ValueError("requirement_text must be a nonempty string")

        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=self._instructions,
                input=requirement_text,
                text_format=StructuredAnalysis,
                store=False,
            )
        except APIError as exc:
            raise AnalyzerAPIError(f"OpenAI Responses API failed: {exc}") from exc
        except ValidationError as exc:
            raise AnalyzerValidationError(
                f"OpenAI structured output failed validation: {exc}"
            ) from exc

        for output in response.output:
            if output.type == "message":
                for content in output.content:
                    if content.type == "refusal":
                        raise AnalyzerRefusalError(
                            f"OpenAI refused the requirement: {content.refusal}"
                        )

        parsed = response.output_parsed
        if parsed is None:
            raise EmptyAnalyzerResponseError(
                f"OpenAI returned no parsed diagram (status: {response.status})"
            )
        if parsed.diagram is None:
            raise InsufficientRequirementError(
                parsed.insufficient_reason or "Requirement contains no supported components"
            )
        if parsed.insufficient_reason is not None:
            raise AnalyzerValidationError(
                "OpenAI returned both a diagram and an insufficiency reason"
            )

        try:
            diagram = parsed.diagram
            return Diagram(
                title=diagram.title,
                diagram_type=diagram.diagram_type,
                direction=diagram.direction,
                groups=tuple(
                    Group(
                        id=group.id,
                        label=group.label,
                        parent_group=group.parent_group,
                    )
                    for group in diagram.groups
                ),
                nodes=tuple(
                    Node(
                        id=node.id,
                        label=node.label,
                        type=node.type,
                        group=node.group,
                        icon=node.icon,
                    )
                    for node in diagram.nodes
                ),
                edges=tuple(
                    Edge(
                        source=edge.source,
                        target=edge.target,
                        label=edge.label,
                        protocol=edge.protocol,
                    )
                    for edge in diagram.edges
                ),
            )
        except ValueError as exc:
            raise AnalyzerValidationError(
                f"OpenAI diagram failed domain validation: {exc}"
            ) from exc
