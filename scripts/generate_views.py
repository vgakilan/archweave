"""Render every view in a diagram plan from one validated source model."""

import argparse
from pathlib import Path

from diagram_generator.pipeline import generate_planned_views


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_json", type=Path, help="validated source diagram model")
    parser.add_argument("plan_json", type=Path, help="diagram view plan")
    args = parser.parse_args()
    for name, source, rendered in generate_planned_views(args.model_json, args.plan_json):
        print(f"{name}: Mermaid: {source}")
        print(f"{name}: SVG: {rendered}")


if __name__ == "__main__":
    main()
