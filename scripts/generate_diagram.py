"""Generate Mermaid and SVG artifacts from any diagram model JSON file."""

import argparse
from pathlib import Path

from diagram_generator.pipeline import generate_diagram


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_json", type=Path, help="path to a diagram model JSON file")
    args = parser.parse_args()
    source, rendered = generate_diagram(args.model_json)
    print(f"Mermaid: {source}")
    print(f"SVG: {rendered}")


if __name__ == "__main__":
    main()
