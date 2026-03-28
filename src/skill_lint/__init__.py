"""skill-lint: Static analysis and quality scoring for Claude Code SKILL.md files."""

from __future__ import annotations

from pathlib import Path

from skill_lint.parser import SkillData, parse_skill
from skill_lint.rules import get_all_rules
from skill_lint.rules.base import RuleDiagnostic
from skill_lint.scorer import ScoreResult, compute_score


def lint(skill_dir: str | Path) -> tuple[SkillData, list[RuleDiagnostic]]:
    """Parse a skill directory and run all rules. Returns (skill_data, diagnostics)."""
    skill_data = parse_skill(skill_dir)
    rules = get_all_rules()
    diagnostics: list[RuleDiagnostic] = []
    for rule in rules:
        diagnostics.extend(rule.check(skill_data))
    return skill_data, diagnostics


def score(skill_dir: str | Path) -> ScoreResult:
    """Parse, lint, and score a skill directory."""
    _, diagnostics = lint(skill_dir)
    return compute_score(diagnostics)


__all__ = ["lint", "score", "SkillData", "ScoreResult", "RuleDiagnostic"]
