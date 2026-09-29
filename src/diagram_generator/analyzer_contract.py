"""Interface for converting requirement text into a validated diagram model."""

from typing import Protocol, runtime_checkable

from diagram_generator.models import Diagram


@runtime_checkable
class RequirementAnalyzer(Protocol):
    """Implementations extract only supported facts from requirement text."""

    def analyze(self, requirement_text: str) -> Diagram:
        """Return a valid Diagram or raise ValueError when extraction is insufficient."""
        ...
