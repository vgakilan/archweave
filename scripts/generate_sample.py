"""Generate and render the sample diagram from its structured model."""

from pathlib import Path

from diagram_generator.pipeline import generate_diagram


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    generate_diagram(root / "diagrams" / "model" / "sample.json", project_root=root)


if __name__ == "__main__":
    main()
