"""CLI entry point for skill-lint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skill_lint import lint
from skill_lint.formatters.json_fmt import format_json
from skill_lint.formatters.terminal import format_terminal
from skill_lint.scorer import compute_score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skill-lint",
        description="Static analysis and quality scoring for Claude Code SKILL.md files",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to skill directories to lint",
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=0,
        help="Exit with error if score is below this threshold",
    )
    args = parser.parse_args(argv)

    exit_code = 0

    for path_str in args.paths:
        path = Path(path_str).resolve()
        if not path.is_dir():
            print(f"Error: {path_str} is not a directory", file=sys.stderr)
            exit_code = 1
            continue

        skill_data, diagnostics = lint(path)
        result = compute_score(diagnostics)
        skill_name = skill_data.name or path.name

        if args.format == "json":
            print(format_json(result, skill_name))
        else:
            print(format_terminal(result, skill_name))

        if result.total < args.fail_under:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
