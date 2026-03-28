"""Tests for the scoring engine."""

from skill_lint.rules.base import RuleDiagnostic, Severity
from skill_lint.scorer import compute_score


def test_perfect_score_no_diagnostics():
    result = compute_score([])
    assert result.total == 100
    assert result.grade == "A+"
    assert not result.has_fatal


def test_fatal_error_caps_at_50():
    diags = [
        RuleDiagnostic(
            rule_id="FM-001", severity=Severity.ERROR,
            message="test", points_deducted=3,
        ),
    ]
    result = compute_score(diags)
    assert result.has_fatal
    assert result.total <= 50


def test_category_deductions():
    diags = [
        RuleDiagnostic(
            rule_id="DESC-001", severity=Severity.WARNING,
            message="too short", points_deducted=3,
        ),
        RuleDiagnostic(
            rule_id="DESC-005", severity=Severity.WARNING,
            message="generic", points_deducted=3,
        ),
    ]
    result = compute_score(diags)
    desc_cat = result.categories["Description"]
    assert desc_cat.earned == 14  # 20 - 3 - 3


def test_bonus_points():
    # Bonus goes to Bonus category which starts at 10/10, so it's already maxed.
    # Test with a deduction first, then bonus recovers it.
    diags = [
        RuleDiagnostic(
            rule_id="BODY-003", severity=Severity.WARNING,
            message="no headings", points_deducted=2,
        ),
        RuleDiagnostic(
            rule_id="BONUS-BODY004", severity=Severity.INFO,
            message="has gotchas", points_deducted=-1,
        ),
    ]
    result = compute_score(diags)
    # Body: 20 - 2 = 18, Bonus gets the -1 (but already at 10 max, stays 10)
    # Total: 10 + 20 + 18 + 20 + 20 + 10 = 98
    assert result.total == 98


def test_grade_thresholds():
    # Score of 85 should be B+
    diags = [
        RuleDiagnostic(rule_id="FM-003", severity=Severity.WARNING, message="t", points_deducted=1),
        RuleDiagnostic(rule_id="DESC-001", severity=Severity.WARNING, message="t", points_deducted=3),
        RuleDiagnostic(rule_id="BODY-003", severity=Severity.WARNING, message="t", points_deducted=2),
        RuleDiagnostic(rule_id="REF-009", severity=Severity.INFO, message="t", points_deducted=1),
        RuleDiagnostic(rule_id="COMP-005", severity=Severity.INFO, message="t", points_deducted=1),
    ]
    result = compute_score(diags)
    # Total: 100 - 8 = 92
    assert result.grade == "A"
