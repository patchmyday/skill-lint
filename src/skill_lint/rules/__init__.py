"""Rule registry: collects all rules from submodules."""

from skill_lint.rules.base import BaseRule
from skill_lint.rules.frontmatter import ALL_RULES as FM_RULES
from skill_lint.rules.description import ALL_RULES as DESC_RULES
from skill_lint.rules.body import ALL_RULES as BODY_RULES
from skill_lint.rules.references import ALL_RULES as REF_RULES
from skill_lint.rules.completeness import ALL_RULES as COMP_RULES


def get_all_rules() -> list[BaseRule]:
    """Return all registered rules."""
    return FM_RULES + DESC_RULES + BODY_RULES + REF_RULES + COMP_RULES
