import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASSETTES = ROOT / "cassettes"


@pytest.mark.skipif(
    not CASSETTES.exists() or not list(CASSETTES.glob("*.jsonl")),
    reason="sin cassettes: corre scripts/record_tape_opencode.py",
)
def test_replay_dataset_commit_generator() -> None:
    proc = subprocess.run(
        [sys.executable, "-c", """
import json, sys
from pathlib import Path
from llm_client import CompletionRequest, CompletionResult, LlmClient, ReplayProvider
from test_kit import EvalCase, EvalDataset, run
from commit_cli.main import load_prompt, render_prompt

ROOT = Path(".").resolve()
dataset = EvalDataset.from_jsonl(ROOT / "evals/commit-message-generator.jsonl")
provider = ReplayProvider(ROOT / "cassettes", record=False)
pid, pv, _ = load_prompt()
client = LlmClient(provider, consumer_repo="commit-cli", model_aliases={"fast": "opencode/big-pickle"}, renderer=render_prompt)
def judge(case: EvalCase) -> CompletionResult:
    return client.complete(CompletionRequest(prompt_id=case.prompt_id, prompt_version=case.prompt_version, variables=case.input, model_alias="fast"))
report = run(dataset, judge, mode="full", threshold=1.0)
assert report.threshold_ok, report.model_dump()
assert report.total == 3
"""],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.returncode == 0