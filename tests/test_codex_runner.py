import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from diagram_generator.codex_runner import CodexRunner, CodexRunnerError


def test_codex_runner_reads_json_from_read_only_ephemeral_run() -> None:
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command[:5] == ["codex", "exec", "--sandbox", "read-only", "--ephemeral"]
        assert "--ignore-user-config" in command
        assert command[-1] == "-"
        assert "<parsed_markdown>" in kwargs["input"]
        Path(command[-2]).write_text(json.dumps({"title": "Orders"}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    with patch("diagram_generator.codex_runner.subprocess.run", side_effect=run):
        result = CodexRunner().extract("# Orders\nCustomer sends an order.")
    assert result == {"title": "Orders"}


def test_codex_runner_rejects_non_json_and_failed_process() -> None:
    def invalid(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        Path(command[-2]).write_text("not JSON", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    with patch("diagram_generator.codex_runner.subprocess.run", side_effect=invalid):
        with pytest.raises(CodexRunnerError, match="JSON object"):
            CodexRunner().plan({"nodes": []})
    with patch("diagram_generator.codex_runner.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "failed")):
        with pytest.raises(CodexRunnerError, match="Codex run failed"):
            CodexRunner().extract("# Orders")
