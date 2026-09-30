from pathlib import Path

import anydoc
import pytest

from diagram_generator.document_parser import parse_document


def test_plain_text_is_saved_as_markdown(tmp_path: Path) -> None:
    source = tmp_path / "requirement.txt"
    source.write_text("The customer uses the portal.\n", encoding="utf-8")

    output = parse_document(source, tmp_path / "parsed" / "requirement.md")

    assert output.read_text(encoding="utf-8") == "The customer uses the portal.\n"


def test_anydoc_converts_csv_to_markdown(tmp_path: Path) -> None:
    source = tmp_path / "services.csv"
    source.write_text("component,role\nPortal,application\n", encoding="utf-8")

    output = parse_document(source, tmp_path / "services.md")

    markdown = output.read_text(encoding="utf-8")
    assert "Portal" in markdown
    assert "application" in markdown
    assert "|" in markdown


def test_unsupported_document_fails_without_output(tmp_path: Path) -> None:
    source = tmp_path / "unknown.bin"
    source.write_bytes(b"not a supported document")
    output = tmp_path / "unknown.md"

    with pytest.raises(anydoc.UnsupportedError):
        parse_document(source, output)

    assert not output.exists()


def test_empty_document_fails_without_output(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text(" \n", encoding="utf-8")
    output = tmp_path / "empty.md"

    with pytest.raises(ValueError, match="no readable text"):
        parse_document(source, output)

    assert not output.exists()


def test_hosted_ocr_is_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-1.4")
    calls: list[tuple[Path, str]] = []

    def fake_to_markdown(path: Path, *, ocr: str) -> str:
        calls.append((path, ocr))
        return "# Requirement"

    monkeypatch.setattr(anydoc, "to_markdown", fake_to_markdown)

    parse_document(source, tmp_path / "local.md")
    parse_document(source, tmp_path / "hosted.md", ocr="hosted")

    assert calls == [(source, "reject"), (source, "hosted")]


def test_output_cannot_overwrite_source(tmp_path: Path) -> None:
    source = tmp_path / "requirement.md"
    source.write_text("# Requirement\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cannot overwrite"):
        parse_document(source, source)

    assert source.read_text(encoding="utf-8") == "# Requirement\n"
