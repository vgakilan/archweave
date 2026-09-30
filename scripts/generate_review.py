"""Render a planned review package from a validated requirement model."""

import argparse

from diagram_generator.review_package import generate_review_package


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="Evidence-backed requirement model JSON")
    parser.add_argument("plan", help="Review view plan JSON")
    args = parser.parse_args()
    for path in generate_review_package(args.model, args.plan):
        print(path)


if __name__ == "__main__":
    main()
