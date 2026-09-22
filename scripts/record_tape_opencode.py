from pathlib import Path

from llm_client import CompletionRequest, CompletionResult, LlmClient, ReplayProvider
from llm_client.providers.opencode_cli import OpenCodeCLI
from test_kit import EvalCase, EvalDataset, run

from commit_cli.main import DEFAULT_MODEL, load_prompt, render_prompt

ROOT = Path(__file__).resolve().parents[1]
CASSETTES = ROOT / "cassettes"


def main() -> None:
    dataset = EvalDataset.from_jsonl(ROOT / "evals" / "commit-message-generator.jsonl")
    recorder = ReplayProvider(CASSETTES, record=True, inner=OpenCodeCLI(DEFAULT_MODEL))
    prompt_id, prompt_version, _ = load_prompt()
    client = LlmClient(
        recorder,
        consumer_repo="commit-cli",
        model_aliases={"fast": DEFAULT_MODEL},
        renderer=render_prompt,
    )

    def judge(case: EvalCase) -> CompletionResult:
        return client.complete(
            CompletionRequest(
                prompt_id=case.prompt_id,
                prompt_version=case.prompt_version,
                variables=case.input,
                model_alias="fast",
                tags=["record", "retrofit-week6"],
            )
        )

    report = run(dataset, judge, mode="full", threshold=1.0)
    print(f"grabadas {len(dataset.cases)} respuestas; pass={report.passed}/{report.total}")
    for case_report in report.cases:
        print(case_report.model_dump())


if __name__ == "__main__":
    main()