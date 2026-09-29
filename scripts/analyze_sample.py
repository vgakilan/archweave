"""Analyze the sample requirement without changing the reference model."""

from pathlib import Path

from diagram_generator.loader import save_diagram
from diagram_generator.openai_analyzer import OpenAIRequirementAnalyzer


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    requirement = (root / "requirements" / "sample.txt").read_text(encoding="utf-8")
    diagram = OpenAIRequirementAnalyzer().analyze(requirement)
    output = save_diagram(diagram, root / "diagrams" / "model" / "sample.generated.json")
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
