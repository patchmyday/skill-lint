"""Colored terminal output formatter."""

from __future__ import annotations

from skill_lint.rules.base import Severity
from skill_lint.scorer import ScoreResult

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

SEVERITY_COLORS = {
    Severity.ERROR: RED,
    Severity.WARNING: YELLOW,
    Severity.INFO: CYAN,
}

SEVERITY_ICONS = {
    Severity.ERROR: "✗",
    Severity.WARNING: "⚠",
    Severity.INFO: "ℹ",
}


def _bar(earned: float, max_pts: float, width: int = 20) -> str:
    """Render a colored progress bar."""
    if max_pts == 0:
        ratio = 1.0
    else:
        ratio = max(0, min(1, earned / max_pts))
    filled = int(ratio * width)
    empty = width - filled

    if ratio >= 0.8:
        color = GREEN
    elif ratio >= 0.5:
        color = YELLOW
    else:
        color = RED

    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def _grade_color(grade: str) -> str:
    if grade.startswith("A"):
        return GREEN
    elif grade.startswith("B"):
        return CYAN
    elif grade.startswith("C"):
        return YELLOW
    return RED


def format_terminal(result: ScoreResult, skill_name: str = "") -> str:
    """Format a score result for terminal display."""
    lines: list[str] = []

    # Header
    header = f"skill-lint report"
    if skill_name:
        header += f": {BOLD}{skill_name}{RESET}"
    lines.append(f"\n{BOLD}{'─' * 60}{RESET}")
    lines.append(header)
    lines.append(f"{BOLD}{'─' * 60}{RESET}")

    # Categories
    for cat_name, cat in result.categories.items():
        if cat_name == "Bonus":
            continue  # Show bonus in total
        bar = _bar(cat.earned, cat.max_points)
        score_str = f"{cat.earned:.0f}/{cat.max_points:.0f}"
        lines.append(f"  {cat_name:<14} {bar} {score_str:>6}")

        # Show diagnostics for this category
        for d in cat.diagnostics:
            sev_color = SEVERITY_COLORS.get(d.severity, "")
            icon = SEVERITY_ICONS.get(d.severity, "")
            line_info = f" (line {d.line})" if d.line else ""
            lines.append(f"    {sev_color}{icon} {d.rule_id}{RESET}: {d.message}{line_info}")
            if d.fix_hint:
                lines.append(f"      {DIM}→ {d.fix_hint}{RESET}")

    # Show bonus category if it has diagnostics
    bonus_cat = result.categories.get("Bonus")
    if bonus_cat and bonus_cat.diagnostics:
        lines.append(f"  {'Bonus':<14}")
        for d in bonus_cat.diagnostics:
            lines.append(f"    {CYAN}★{RESET} {d.message}")

    # Summary
    lines.append(f"\n{BOLD}{'─' * 60}{RESET}")
    gc = _grade_color(result.grade)
    lines.append(f"  {BOLD}Score: {result.total:.0f}/100  Grade: {gc}{result.grade}{RESET}")
    if result.has_fatal:
        lines.append(f"  {RED}⚠ Fatal errors present — score capped at 50{RESET}")
    lines.append(f"{BOLD}{'─' * 60}{RESET}\n")

    return "\n".join(lines)
