"""Description analysis rules (DESC-001 through DESC-012)."""

from __future__ import annotations

import re

from skill_lint.parser import SkillData
from skill_lint.rules.base import BaseRule, RuleDiagnostic, Severity
from skill_lint.wordlists import (
    ANTI_TRIGGER_PHRASES,
    GENERIC_WORDS,
    SPECIFICITY_MARKERS,
    TRIGGER_PHRASES,
)


class DESC001_MinWordCount(BaseRule):
    rule_id = "DESC-001"
    description = "description should have at least 15 words"
    category = "Description"
    severity = Severity.WARNING
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        wc = len(skill_data.description.split())
        if wc < 15:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Description has only {wc} words (minimum 15 recommended)",
                fix_hint="Expand your description with trigger conditions and use cases",
                points_deducted=self.max_points,
            )]
        return []


class DESC002_SweetSpot(BaseRule):
    rule_id = "DESC-002"
    description = "description word count in sweet spot (50-100 words)"
    category = "Description"
    severity = Severity.INFO
    max_points = 0  # bonus rule

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        wc = len(skill_data.description.split())
        if 50 <= wc <= 100:
            return [RuleDiagnostic(
                rule_id="BONUS-DESC002",
                severity=Severity.INFO,
                message=f"Description length ({wc} words) is in the sweet spot",
                points_deducted=-2,  # bonus
            )]
        return []


class DESC003_HasTriggerPhrases(BaseRule):
    rule_id = "DESC-003"
    description = "description should contain trigger phrases"
    category = "Description"
    severity = Severity.WARNING
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        desc_lower = skill_data.description.lower()
        found = any(tp.lower() in desc_lower for tp in TRIGGER_PHRASES)
        if not found:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="No trigger phrases found in description",
                fix_hint=f"Add phrases like: {', '.join(TRIGGER_PHRASES[:3])}",
                points_deducted=self.max_points,
            )]
        return []


class DESC004_HasAntiTrigger(BaseRule):
    rule_id = "DESC-004"
    description = "description should have anti-trigger phrases"
    category = "Description"
    severity = Severity.INFO
    max_points = 0  # bonus

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        desc_lower = skill_data.description.lower()
        found = any(ap.lower() in desc_lower for ap in ANTI_TRIGGER_PHRASES)
        if found:
            return [RuleDiagnostic(
                rule_id="BONUS-DESC004",
                severity=Severity.INFO,
                message="Has anti-trigger phrases (reduces false activations)",
                points_deducted=-2,  # bonus
            )]
        return []


class DESC005_GenericWordRatio(BaseRule):
    rule_id = "DESC-005"
    description = "description should not be overly generic"
    category = "Description"
    severity = Severity.WARNING
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        words = re.findall(r"\w+", skill_data.description.lower())
        if not words:
            return []
        generic_count = sum(1 for w in words if w in GENERIC_WORDS)
        ratio = generic_count / len(words)
        if ratio > 0.3:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"High generic word ratio ({ratio:.0%}): too vague for reliable triggering",
                fix_hint="Replace generic words with specific tool names, file types, or domain terms",
                points_deducted=self.max_points,
            )]
        return []


class DESC006_FirstSentence(BaseRule):
    rule_id = "DESC-006"
    description = "first sentence should describe purpose directly"
    category = "Description"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        first_word = skill_data.description.strip().split()[0].lower() if skill_data.description.strip() else ""
        weak_starts = ["a", "an", "the", "this", "it"]
        if first_word in weak_starts:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Description starts with '{first_word}' — prefer an action verb",
                fix_hint="Start with a verb: 'Create...', 'Analyze...', 'Use when...'",
                points_deducted=self.max_points,
            )]
        return []


class DESC007_HasExamples(BaseRule):
    rule_id = "DESC-007"
    description = "description should contain example scenarios"
    category = "Description"
    severity = Severity.INFO
    max_points = 0  # bonus

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        desc_lower = skill_data.description.lower()
        example_markers = [
            "e.g.", "for example", "such as", "like:", "includes:",
            "example:", "for instance", "triggers include",
        ]
        if any(m in desc_lower for m in example_markers):
            return [RuleDiagnostic(
                rule_id="BONUS-DESC007",
                severity=Severity.INFO,
                message="Description includes example scenarios",
                points_deducted=-1,  # bonus
            )]
        return []


class DESC008_DualAudience(BaseRule):
    rule_id = "DESC-008"
    description = "description should serve both humans and trigger logic"
    category = "Description"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        desc_lower = skill_data.description.lower()
        has_trigger = any(tp.lower() in desc_lower for tp in TRIGGER_PHRASES)
        # Check for human-readable explanation (has sentences ending in periods)
        has_explanation = bool(re.search(r"[A-Z][^.!?]*[.!?]", skill_data.description))
        if has_trigger and has_explanation:
            return []
        if not has_trigger and not has_explanation:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Description lacks both trigger conditions and human explanation",
                fix_hint="Include both a plain explanation AND trigger phrases (e.g., 'Use when...')",
                points_deducted=self.max_points,
            )]
        if not has_trigger:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Description has explanation but no trigger conditions",
                fix_hint="Add trigger phrases like 'Use when...', 'TRIGGER when...'",
                points_deducted=1,
            )]
        return []


class DESC009_NoYamlMultiline(BaseRule):
    rule_id = "DESC-009"
    description = "description should not use YAML multiline indicators"
    category = "Description"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.raw_frontmatter:
            return []
        # Check if the raw description value in frontmatter starts with >- or |
        raw_desc = skill_data.raw_frontmatter.get("description", "")
        if isinstance(raw_desc, str) and (raw_desc.startswith(">") or raw_desc.startswith("|")):
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Description uses YAML multiline indicator (>- or |)",
                fix_hint="Use a simple quoted string for the description field",
                points_deducted=self.max_points,
            )]
        return []


class DESC010_NoNameRepeat(BaseRule):
    rule_id = "DESC-010"
    description = "description should not repeat name as first word"
    category = "Description"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description or not skill_data.name:
            return []
        first_word = skill_data.description.strip().split()[0].lower().rstrip(".:,;")
        if first_word == skill_data.name.lower():
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Description starts with the skill name",
                fix_hint="Start the description with what the skill does, not its name",
                points_deducted=self.max_points,
            )]
        return []


class DESC011_ApproachingLimit(BaseRule):
    rule_id = "DESC-011"
    description = "warning if description > 900 chars"
    category = "Description"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        if len(skill_data.description) > 900:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Description is {len(skill_data.description)} chars (approaching 1024 limit)",
                fix_hint="Consider trimming — move detailed instructions to the body",
                points_deducted=self.max_points,
            )]
        return []


class DESC012_SpecificityMarkers(BaseRule):
    rule_id = "DESC-012"
    description = "description should contain specificity markers"
    category = "Description"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.description:
            return []
        found = any(m in skill_data.description for m in SPECIFICITY_MARKERS)
        if not found:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="No specificity markers (file types, tool names, frameworks) found",
                fix_hint="Mention specific file extensions (.pdf, .py), tool names, or frameworks",
                points_deducted=self.max_points,
            )]
        return []


ALL_RULES = [
    DESC001_MinWordCount(),
    DESC002_SweetSpot(),
    DESC003_HasTriggerPhrases(),
    DESC004_HasAntiTrigger(),
    DESC005_GenericWordRatio(),
    DESC006_FirstSentence(),
    DESC007_HasExamples(),
    DESC008_DualAudience(),
    DESC009_NoYamlMultiline(),
    DESC010_NoNameRepeat(),
    DESC011_ApproachingLimit(),
    DESC012_SpecificityMarkers(),
]
