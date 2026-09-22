from __future__ import annotations

import argparse
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import yaml

from llm_client import CompletionRequest, LlmClient, ReplayProvider, Span
from llm_client.providers.opencode_cli import OpenCodeCLI

DEFAULT_MODEL = "opencode/big-pickle"
ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = ROOT / "prompts" / "commit-message-generator.md"


def load_prompt() -> tuple[str, str, str]:
    text = PROMPT_FILE.read_text()
    if not text.startswith("---"):
        raise SystemExit(f"{PROMPT_FILE}: falta frontmatter")
    _, frontmatter, body = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    return data["id"], data["version"], body.strip()


def render_prompt(prompt_id: str, prompt_version: str, variables: dict) -> list[dict]:
    _, _, body = load_prompt()
    system_part = body.split("## Sistema\n", 1)[1].split("## Usuario\n", 1)[0].strip()
    user_part = body.split("## Usuario\n", 1)[1].strip().format(
        diff=variables["diff"],
        language=variables.get("language", "es"),
    )
    return [
        {"role": "system", "content": system_part},
        {"role": "user", "content": user_part},
    ]


def git_diff(root: Path, staged: bool) -> str:
    cmd = ["git", "-C", str(root), "diff"]
    if staged:
        cmd.append("--cached")
    cmd += ["--", ".", ":(exclude)uv.lock"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(1)
    return proc.stdout


def build_emitter(span_file: Path | None):
    def emit(span: Span, _result) -> None:
        if span_file is not None:
            with span_file.open("a") as handle:
                handle.write(span.as_jsonl() + "\n")
        else:
            sys.stderr.write(span.as_jsonl() + "\n")

    return emit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="commit-cli", description="Propone mensaje de commit con llm-client")
    parser.add_argument("--staged", action="store_true", help="usar git diff --cached")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"modelo opencode (default: {DEFAULT_MODEL})")
    parser.add_argument("--replay", metavar="DIR", default=None, help="reproducir cassettes en vez de llamar al LLM")
    parser.add_argument("--span-file", metavar="PATH", default=None, help="escribir spans a un archivo JSONL")
    parser.add_argument("--cost-cap", metavar="USD", type=Decimal, default=None, help="costo semanal por llamada")
    parser.add_argument("--git-dir", default=None, help="raíz del repo a inspeccionar (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.git_dir).resolve() if args.git_dir else Path.cwd()
    diff = git_diff(root, args.staged)
    if not diff.strip():
        sys.stderr.write("commit-cli: no hay cambios en el árbol (sin salida de git diff)\n")
        return 1

    if args.replay:
        provider = ReplayProvider(args.replay, record=False)
    else:
        provider = OpenCodeCLI(args.model, cwd=str(root))

    prompt_id, prompt_version, _ = load_prompt()
    client = LlmClient(
        provider,
        consumer_repo="commit-cli",
        model_aliases={"fast": args.model},
        emitter=build_emitter(Path(args.span_file) if args.span_file else None),
        cost_cap_usd=args.cost_cap,
        renderer=render_prompt,
    )
    result = client.complete(
        CompletionRequest(
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            variables={"diff": diff, "language": "es"},
            model_alias="fast",
            tags=["commit-cli", "week-2"],
        )
    )

    if not result.validation.ok:
        sys.stderr.write(f"commit-cli: respuesta no válida ({', '.join(result.validation.errors)})\n")
        return 2

    print(result.raw_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())