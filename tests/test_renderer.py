import os
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from diagram_generator.renderer import MermaidRenderError, render_mermaid


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source.mmd"
    source.write_text("flowchart LR\n    a --> b\n", encoding="utf-8")
    output = tmp_path / "rendered" / "sample.svg"
    cli_name = "mmdc.cmd" if os.name == "nt" else "mmdc"
    cli = tmp_path / "node_modules" / ".bin" / cli_name
    cli.parent.mkdir(parents=True)
    cli.touch()
    return source, output, cli


def test_renderer_uses_local_cli_and_returns_svg(tmp_path: Path) -> None:
    source, output, cli = _setup(tmp_path)

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output.parent.mkdir(parents=True, exist_ok=True)
        Path(command[-1]).write_text("<svg/>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "rendered", "")

    with patch("diagram_generator.renderer.subprocess.run", side_effect=run) as mock_run:
        result = render_mermaid(source, output, project_root=tmp_path)

    assert result == output
    assert output.read_text(encoding="utf-8") == "<svg/>"
    args, kwargs = mock_run.call_args
    assert args[0][:4] == [str(cli), "-i", str(source), "-o"]
    assert Path(args[0][4]).parent == output.parent
    assert Path(args[0][4]).suffix == ".svg"
    assert kwargs["cwd"] == tmp_path
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True


def test_renderer_registers_only_local_packs_used_by_source(tmp_path: Path) -> None:
    source, output, cli = _setup(tmp_path)
    source.write_text(
        'flowchart LR\n    n@{ shape: icon, icon: "lucide:user-round", label: "User" }\n',
        encoding="utf-8",
    )

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output.parent.mkdir(parents=True, exist_ok=True)
        Path(command[-1]).write_text("<svg/>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    with patch("diagram_generator.renderer.subprocess.run", side_effect=run) as mock_run:
        render_mermaid(source, output, project_root=tmp_path)

    command = mock_run.call_args.args[0]
    assert command == [
        str(cli), "--iconPacks", "@iconify-json/lucide", "-i", str(source),
        "-o", command[-1],
    ]


def test_renderer_reports_cli_failure(tmp_path: Path) -> None:
    source, output, _ = _setup(tmp_path)
    failed = subprocess.CompletedProcess([], 1, "rendering started", "invalid diagram")

    with patch("diagram_generator.renderer.subprocess.run", return_value=failed):
        with pytest.raises(MermaidRenderError) as error:
            render_mermaid(source, output, project_root=tmp_path)

    assert "exit code 1" in str(error.value)
    assert "rendering started" in str(error.value)
    assert "invalid diagram" in str(error.value)


def test_renderer_requires_local_cli(tmp_path: Path) -> None:
    source, output, cli = _setup(tmp_path)
    cli.unlink()

    with pytest.raises(FileNotFoundError, match="Local Mermaid CLI not found"):
        render_mermaid(source, output, project_root=tmp_path)


def test_renderer_rejects_missing_svg(tmp_path: Path) -> None:
    source, output, _ = _setup(tmp_path)
    output.parent.mkdir()
    output.write_text("old SVG", encoding="utf-8")
    succeeded = subprocess.CompletedProcess([], 0, "done", "")

    with patch("diagram_generator.renderer.subprocess.run", return_value=succeeded):
        with pytest.raises(MermaidRenderError, match="produced no SVG"):
            render_mermaid(source, output, project_root=tmp_path)

    assert output.read_text(encoding="utf-8") == "old SVG"
