"""JSON output formatter."""

from __future__ import annotations

import json

from skill_lint.scorer import ScoreResult


def format_json(result: ScoreResult, skill_name: str = "") -> str:
    """Format a score result as JSON."""
    data = {
        "skill": skill_name,
        "score": result.total,
        "grade": result.grade,
        "has_fatal": result.has_fatal,
        "categories": {},
        "diagnostics": [],
    }

    for cat_name, cat in result.categories.items():
        data["categories"][cat_name] = {
            "earned": cat.earned,
            "max": cat.max_points,
        }

    for d in result.diagnostics:
        data["diagnostics"].append({
            "rule_id": d.rule_id,
            "severity": d.severity.value,
            "message": d.message,
            "fix_hint": d.fix_hint,
            "line": d.line,
            "points_deducted": d.points_deducted,
        })

    return json.dumps(data, indent=2)
