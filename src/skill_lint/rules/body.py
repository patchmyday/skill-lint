"""Body content rules (BODY-001 through BODY-010)."""

from __future__ import annotations

import re

from skill_lint.parser import SkillData
from skill_lint.rules.base import BaseRule, RuleDiagnostic, Severity


class BODY001_NotEmpty(BaseRule):
    rule_id = "BODY-001"
    description = "body must not be empty"
    category = "Body"
    severity = Severity.ERROR
    max_points = 5

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text.strip():
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="SKILL.md body is empty — no instructions for the agent",
                fix_hint="Add sections with instructions, examples, and guidelines",
                points_deducted=self.max_points,
            )]
        return []


class BODY002_LineCountMax(BaseRule):
    rule_id = "BODY-002"
    description = "body should be under 500 lines"
    category = "Body"
    severity = Severity.WARNING
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        lc = len(skill_data.body_lines)
        if lc > 500:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Body is {lc} lines (over 500) — wastes context window tokens",
                fix_hint="Move detailed content to references/ files",
                points_deducted=self.max_points,
            )]
        return []


class BODY003_HasHeadings(BaseRule):
    rule_id = "BODY-003"
    description = "body should have section headings"
    category = "Body"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text.strip():
            return []
        headings = [l for l in skill_data.body_lines if re.match(r"^#{2,3}\s", l)]
        if not headings:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="No section headings (## or ###) found in body",
                fix_hint="Organize content with markdown headings for better readability",
                points_deducted=self.max_points,
            )]
        return []


class BODY004_HasGotchas(BaseRule):
    rule_id = "BODY-004"
    description = "body should have gotchas/pitfalls section"
    category = "Body"
    severity = Severity.INFO
    max_points = 0  # bonus

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        body_lower = skill_data.body_text.lower()
        markers = ["gotcha", "pitfall", "common mistake", "watch out", "caveat",
                    "important note", "warning", "caution", "troubleshoot"]
        if any(m in body_lower for m in markers):
            return [RuleDiagnostic(
                rule_id="BONUS-BODY004",
                severity=Severity.INFO,
                message="Has gotchas/pitfalls section — helps agents avoid common mistakes",
                points_deducted=-1,
            )]
        return []


class BODY005_ProgressiveDisclosure(BaseRule):
    rule_id = "BODY-005"
    description = "body should use progressive disclosure"
    category = "Body"
    severity = Severity.INFO
    max_points = 0  # bonus

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        body_lower = skill_data.body_text.lower()
        if "references/" in body_lower or "scripts/" in body_lower:
            return [RuleDiagnostic(
                rule_id="BONUS-BODY005",
                severity=Severity.INFO,
                message="Uses progressive disclosure (references/ or scripts/)",
                points_deducted=-1,
            )]
        return []


class BODY006_NoTodoMarkers(BaseRule):
    rule_id = "BODY-006"
    description = "no TODO/FIXME/HACK markers in body"
    category = "Body"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        results = []
        for i, line in enumerate(skill_data.body_lines, 1):
            for marker in ["TODO", "FIXME", "HACK", "XXX"]:
                if marker in line:
                    results.append(RuleDiagnostic(
                        rule_id=self.rule_id, severity=self.severity,
                        message=f"Found {marker} marker on line {i}",
                        fix_hint="Resolve or remove TODO/FIXME markers before publishing",
                        line=i,
                        points_deducted=0.5,
                    ))
        return results


class BODY007_HasExamples(BaseRule):
    rule_id = "BODY-007"
    description = "body should have examples or code blocks"
    category = "Body"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        has_code_blocks = "```" in skill_data.body_text
        has_example_marker = any(
            m in skill_data.body_text.lower()
            for m in ["example", "e.g.", "for instance", "sample"]
        )
        if not has_code_blocks and not has_example_marker:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="No examples or code blocks found in body",
                fix_hint="Add concrete examples or code blocks to guide agent behavior",
                points_deducted=self.max_points,
            )]
        return []


class BODY008_FirstSectionOverview(BaseRule):
    rule_id = "BODY-008"
    description = "first section should be overview/when-to-use"
    category = "Body"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        # Find first heading
        for line in skill_data.body_lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                heading_lower = stripped.lower()
                good_starts = ["overview", "when to use", "about", "introduction",
                               "what is", "purpose", "quick start", "getting started"]
                # Just check if any good start is a substring of heading text
                heading_text = re.sub(r"^#+\s*", "", heading_lower)
                if any(gs in heading_text for gs in good_starts):
                    return []
                return [RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"First heading '{stripped}' isn't an overview section",
                    fix_hint="Start with '## Overview' or '## When to Use'",
                    points_deducted=self.max_points,
                )]
        return []


class BODY009_LineCountWarning(BaseRule):
    rule_id = "BODY-009"
    description = "line count warning if > 300"
    category = "Body"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        lc = len(skill_data.body_lines)
        if 300 < lc <= 500:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Body is {lc} lines (approaching 500 limit)",
                fix_hint="Consider moving some content to references/ files",
                points_deducted=self.max_points,
            )]
        return []


class BODY010_NoDuplicateHeadings(BaseRule):
    rule_id = "BODY-010"
    description = "no duplicate headings"
    category = "Body"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        headings = []
        for line in skill_data.body_lines:
            if re.match(r"^#{1,6}\s", line):
                headings.append(line.strip().lower())
        seen = set()
        dupes = []
        for h in headings:
            if h in seen:
                dupes.append(h)
            seen.add(h)
        if dupes:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Duplicate headings found: {', '.join(dupes[:3])}",
                fix_hint="Use unique heading names",
                points_deducted=self.max_points,
            )]
        return []


ALL_RULES = [
    BODY001_NotEmpty(),
    BODY002_LineCountMax(),
    BODY003_HasHeadings(),
    BODY004_HasGotchas(),
    BODY005_ProgressiveDisclosure(),
    BODY006_NoTodoMarkers(),
    BODY007_HasExamples(),
    BODY008_FirstSectionOverview(),
    BODY009_LineCountWarning(),
    BODY010_NoDuplicateHeadings(),
]
