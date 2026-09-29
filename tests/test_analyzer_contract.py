from pathlib import Path

from diagram_generator.analyzer_contract import RequirementAnalyzer
from diagram_generator.loader import load_diagram
from diagram_generator.models import Diagram


SAMPLE_MODEL = Path(__file__).resolve().parents[1] / "diagrams" / "model" / "sample.json"


class SampleAnalyzer:
    def analyze(self, requirement_text: str) -> Diagram:
        return load_diagram(SAMPLE_MODEL)


def test_analyzer_interface_accepts_compatible_implementation() -> None:
    analyzer: RequirementAnalyzer = SampleAnalyzer()

    assert isinstance(analyzer, RequirementAnalyzer)
    assert isinstance(analyzer.analyze("sample requirement"), Diagram)


def test_analyzer_interface_rejects_missing_analyze_method() -> None:
    assert not isinstance(object(), RequirementAnalyzer)
