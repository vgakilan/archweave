import json
from pathlib import Path
from unittest.mock import patch

import pytest

from diagram_generator.pipeline import generate_diagram, output_paths
from diagram_generator.renderer import MermaidRenderError


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "diagrams" / "model" / "sample.json"


def test_output_paths_preserve_dotted_model_stem(tmp_path: Path) -> None:
    source, rendered = output_paths(
        "diagrams/model/order_processing.generated.json", project_root=tmp_path
    )

    assert source == tmp_path / "diagrams" / "source" / "order_processing.generated.mmd"
    assert rendered == tmp_path / "diagrams" / "rendered" / "order_processing.generated.svg"


def test_generate_valid_model(tmp_path: Path) -> None:
    model = tmp_path / "sample.json"
    model.write_bytes(SAMPLE.read_bytes())

    def render(source: Path, output: Path, *, project_root: Path) -> Path:
        assert project_root == tmp_path
        assert source.is_file()
        output.parent.mkdir(parents=True)
        output.write_text("<svg/>", encoding="utf-8")
        return output

    with patch("diagram_generator.pipeline.render_mermaid", side_effect=render) as mock:
        source, rendered = generate_diagram(model, project_root=tmp_path)

    assert "flowchart LR" in source.read_text(encoding="utf-8")
    assert "Order requests" in source.read_text(encoding="utf-8")
    assert rendered.read_text(encoding="utf-8") == "<svg/>"
    mock.assert_called_once_with(source, rendered, project_root=tmp_path)


def test_generate_rejects_missing_model(tmp_path: Path) -> None:
    with patch("diagram_generator.pipeline.render_mermaid") as render:
        with pytest.raises(FileNotFoundError, match="Diagram model file not found"):
            generate_diagram(tmp_path / "missing.json", project_root=tmp_path)

    assert not (tmp_path / "diagrams").exists()
    render.assert_not_called()


def test_generate_rejects_invalid_model_before_writing(tmp_path: Path) -> None:
    model = tmp_path / "invalid.json"
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    data["edges"][0]["target"] = "nonexistent"
    model.write_text(json.dumps(data), encoding="utf-8")

    with patch("diagram_generator.pipeline.render_mermaid") as render:
        with pytest.raises(ValueError, match="references unknown node ID"):
            generate_diagram(model, project_root=tmp_path)

    assert not (tmp_path / "diagrams").exists()
    render.assert_not_called()


def test_generate_propagates_render_failure(tmp_path: Path) -> None:
    model = tmp_path / "sample.json"
    model.write_bytes(SAMPLE.read_bytes())

    with patch(
        "diagram_generator.pipeline.render_mermaid",
        side_effect=MermaidRenderError("Mermaid CLI failed"),
    ):
        with pytest.raises(MermaidRenderError, match="Mermaid CLI failed"):
            generate_diagram(model, project_root=tmp_path)

    assert (tmp_path / "diagrams" / "source" / "sample.mmd").is_file()
    assert not (tmp_path / "diagrams" / "rendered" / "sample.svg").exists()
