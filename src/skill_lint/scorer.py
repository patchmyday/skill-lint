"""Scoring engine: aggregates rule diagnostics into category scores and a grade."""

from __future__ import annotations

from dataclasses import dataclass, field

from skill_lint.rules.base import RuleDiagnostic, Severity

CATEGORY_WEIGHTS: dict[str, float] = {
    "Frontmatter": 10,
    "Description": 20,
    "Body": 20,
    "References": 20,
    "Completeness": 20,
    "Bonus": 10,
}

GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (95, "A+"),
    (90, "A"),
    (85, "B+"),
    (80, "B"),
    (75, "C+"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
]


@dataclass
class CategoryScore:
    name: str
    max_points: float
    earned: float
    diagnostics: list[RuleDiagnostic] = field(default_factory=list)


@dataclass
class ScoreResult:
    categories: dict[str, CategoryScore] = field(default_factory=dict)
    total: float = 0
    max_total: float = 100
    grade: str = "F"
    has_fatal: bool = False
    diagnostics: list[RuleDiagnostic] = field(default_factory=list)


def compute_score(diagnostics: list[RuleDiagnostic]) -> ScoreResult:
    """Compute the overall score from a list of rule diagnostics."""
    result = ScoreResult(diagnostics=diagnostics)

    # Initialize categories
    for cat_name, max_pts in CATEGORY_WEIGHTS.items():
        result.categories[cat_name] = CategoryScore(
            name=cat_name, max_points=max_pts, earned=max_pts
        )

    # Map rule prefixes to categories
    prefix_map = {
        "FM": "Frontmatter",
        "DESC": "Description",
        "BODY": "Body",
        "REF": "References",
        "COMP": "Completeness",
        "BONUS": "Bonus",
    }

    # Check for fatal errors
    has_fatal = any(d.severity == Severity.ERROR for d in diagnostics)
    result.has_fatal = has_fatal

    # Apply deductions
    for diag in diagnostics:
        prefix = diag.rule_id.split("-")[0]
        cat_name = prefix_map.get(prefix)
        if cat_name and cat_name in result.categories:
            cat = result.categories[cat_name]
            if diag.points_deducted > 0:
                cat.earned = max(0, cat.earned - diag.points_deducted)
            elif diag.points_deducted < 0:
                # Negative deduction = bonus points
                cat.earned = min(cat.max_points, cat.earned - diag.points_deducted)
            cat.diagnostics.append(diag)

    # Compute total
    total = sum(cat.earned for cat in result.categories.values())

    # Fatal errors cap at 50
    if has_fatal:
        total = min(total, 50)

    result.total = round(total, 1)

    # Determine grade
    for threshold, grade in GRADE_THRESHOLDS:
        if result.total >= threshold:
            result.grade = grade
            break

    return result
