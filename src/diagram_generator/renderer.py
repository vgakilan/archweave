"""Render Mermaid source with the repository's local Mermaid CLI."""

import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from diagram_generator.icons import ICON_PACKAGES


_ICON_PREFIX = re.compile(r'@\{\s*shape:\s*icon,\s*icon:\s*"([a-z][a-z0-9-]*):')

class MermaidRenderError(RuntimeError):
    """The local Mermaid CLI could not produce an SVG."""


def render_mermaid(
    input_path: str | Path,
    output_path: str | Path,
    *,
    project_root: str | Path | None = None,
) -> Path:
    """Render a .mmd file to SVG and return the output path."""
    source = Path(input_path).resolve()
    output = Path(output_path).resolve()
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    cli_name = "mmdc.cmd" if os.name == "nt" else "mmdc"
    cli = root / "node_modules" / ".bin" / cli_name

    if source.suffix.lower() != ".mmd":
        raise ValueError(f"Mermaid input must be a .mmd file: {source}")
    if output.suffix.lower() != ".svg":
        raise ValueError(f"Mermaid output must be a .svg file: {output}")
    if not source.is_file():
        raise FileNotFoundError(f"Mermaid input file not found: {source}")
    if not cli.is_file():
        raise FileNotFoundError(
            f"Local Mermaid CLI not found: {cli}. Run npm install in {root}."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.{uuid4().hex}.svg")
    icon_prefixes = set(_ICON_PREFIX.findall(source.read_text(encoding="utf-8")))
    icon_packages = [
        package for prefix, package in ICON_PACKAGES.items() if prefix in icon_prefixes
    ]
    command = [str(cli)]
    if icon_packages:
        command.extend(["--iconPacks", *icon_packages])
    command.extend(["-i", str(source), "-o", str(temporary_output)])
    try:
        try:
            result = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise MermaidRenderError(
                f"Local Mermaid CLI timed out after {exc.timeout} seconds.\n"
                f"stdout: {exc.stdout or ''}\n"
                f"stderr: {exc.stderr or ''}"
            ) from exc
        except OSError as exc:
            raise MermaidRenderError(f"Could not run local Mermaid CLI: {exc}") from exc

        if result.returncode != 0:
            raise MermaidRenderError(
                f"Mermaid CLI failed with exit code {result.returncode}.\n"
                f"Command: {subprocess.list2cmdline(command)}\n"
                f"stdout: {result.stdout.strip()}\n"
                f"stderr: {result.stderr.strip()}"
            )
        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise MermaidRenderError(
                f"Mermaid CLI exited successfully but produced no SVG: {output}\n"
                f"stdout: {result.stdout.strip()}\n"
                f"stderr: {result.stderr.strip()}"
            )
        temporary_output.replace(output)
    finally:
        temporary_output.unlink(missing_ok=True)
    return output
