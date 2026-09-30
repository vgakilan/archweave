"""Run requirement parsing, Codex analysis, planning, and SVG generation."""

import argparse

from diagram_generator.codex_runner import CodexRunner
from diagram_generator.workflow import run_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="Requirement document or parsed Markdown")
    args = parser.parse_args()
    codex = CodexRunner()
    for artifact in run_workflow(args.document, extract=codex.extract, plan=codex.plan):
        print(artifact)


if __name__ == "__main__":
    main()
