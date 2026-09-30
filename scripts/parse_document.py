"""Convert a requirement document to Markdown for later analysis."""

import argparse
from pathlib import Path

from diagram_generator.document_parser import parse_document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path, help="requirement document to parse")
    parser.add_argument("-o", "--output", type=Path, help="Markdown output path")
    parser.add_argument(
        "--ocr",
        choices=("reject", "hosted"),
        default="reject",
        help="use Firecrawl hosted OCR for scanned PDFs when explicitly selected",
    )
    args = parser.parse_args()
    output = parse_document(args.document, args.output, ocr=args.ocr)
    print(f"Markdown: {output}")


if __name__ == "__main__":
    main()
