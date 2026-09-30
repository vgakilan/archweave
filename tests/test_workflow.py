import json
from pathlib import Path
from unittest.mock import patch

from diagram_generator.workflow import run_workflow
from test_review_package import _input


def test_workflow_runs_extract_plan_and_render_from_markdown(tmp_path: Path) -> None:
    model_file, plan_file = _input(tmp_path)
    model = json.loads(model_file.read_text(encoding="utf-8"))
    view_plan = json.loads(plan_file.read_text(encoding="utf-8"))
    markdown = Path(model["source_markdown"])
    calls = []

    def extract(text: str) -> dict:
        assert "Customer sends an order" in text
        calls.append("extract")
        return model

    def plan(validated: dict) -> dict:
        assert validated["nodes"][0]["name"] == "Customer"
        calls.append("plan")
        return view_plan

    def render(source: Path, output: Path, *, project_root: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("<svg/>", encoding="utf-8")
        calls.append("render")
        return output

    with patch("diagram_generator.review_package.render_mermaid", side_effect=render):
        artifacts = run_workflow(markdown, extract=extract, plan=plan, project_root=tmp_path)

    assert calls == ["extract", "plan", "render", "render", "render"]
    assert artifacts[0] == markdown
    assert artifacts[1].name == "parsed.requirement.json"
    assert artifacts[2].name == "parsed.review.json"
    assert artifacts[-1].is_file()
