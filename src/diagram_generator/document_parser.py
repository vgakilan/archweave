"""Convert requirement documents to Markdown before requirement analysis."""

from pathlib import Path
from typing import Literal

import anydoc


OcrMode = Literal["reject", "hosted"]


def parse_document(
    source_path: str | Path,
    output_path: str | Path | None = None,
    *,
    ocr: OcrMode = "reject",
) -> Path:
    """Save the document's Markdown and return its path.

    Text and Markdown inputs are already readable by the analyzer. AnyDoc
    converts other supported document formats. Conversion failures leave no
    new output file and must be resolved before analysis.
    """
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(f"Requirement document not found: {source}")
    if ocr not in ("reject", "hosted"):
        raise ValueError(f"Unsupported OCR mode: {ocr}")

    if source.suffix.lower() in {".txt", ".md"}:
        markdown = source.read_text(encoding="utf-8-sig")
    else:
        markdown = anydoc.to_markdown(source, ocr=ocr)

    if not markdown.strip():
        raise ValueError(f"Requirement document contains no readable text: {source}")

    root = Path(__file__).resolve().parents[2]
    output = (
        Path(output_path)
        if output_path is not None
        else root / "requirements" / "parsed" / f"{source.name}.md"
    )
    if output.suffix.lower() != ".md":
        raise ValueError(f"Markdown output must be a .md file: {output}")
    if output.resolve() == source.resolve():
        raise ValueError("Markdown output cannot overwrite the source document")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8", newline="\n")
    return output
