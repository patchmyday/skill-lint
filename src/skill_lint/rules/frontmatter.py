"""Frontmatter rules (FM-001 through FM-008)."""

from __future__ import annotations

import re

from skill_lint.parser import SkillData
from skill_lint.rules.base import BaseRule, RuleDiagnostic, Severity


class FM001_NameExists(BaseRule):
    rule_id = "FM-001"
    description = "name field must exist"
    category = "Frontmatter"
    severity = Severity.ERROR
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.name:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Missing 'name' field in frontmatter",
                fix_hint="Add 'name: my-skill-name' to YAML frontmatter",
                points_deducted=self.max_points,
            )]
        return []


class FM002_NameKebabCase(BaseRule):
    rule_id = "FM-002"
    description = "name should be kebab-case"
    category = "Frontmatter"
    severity = Severity.ERROR
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.name:
            return []
        if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", skill_data.name):
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Name '{skill_data.name}' is not kebab-case",
                fix_hint="Use lowercase letters, numbers, and hyphens (e.g., 'my-skill-name')",
                points_deducted=self.max_points,
            )]
        return []


class FM003_NameLength(BaseRule):
    rule_id = "FM-003"
    description = "name should be under 64 characters"
    category = "Frontmatter"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if skill_data.name and len(skill_data.name) >= 64:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Name is {len(skill_data.name)} chars (max 64)",
                fix_hint="Shorten the skill name",
                points_deducted=self.max_points,
            )]
        return []


class FM004_NameMatchesDir(BaseRule):
    rule_id = "FM-004"
    description = "name should match directory name"
    category = "Frontmatter"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.name:
            return []
        dir_name = skill_data.skill_path.name
        if skill_data.name != dir_name:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Name '{skill_data.name}' doesn't match directory '{dir_name}'",
                fix_hint=f"Rename to '{dir_name}' or rename the directory to '{skill_data.name}'",
                points_deducted=self.max_points,
            )]
        return []


class FM005_DescriptionExists(BaseRule):
    rule_id = "FM-005"
    description = "description field must exist"
    category = "Frontmatter"
    severity = Severity.ERROR
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if skill_data.description is None:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Missing 'description' field in frontmatter",
                fix_hint="Add a description field to the YAML frontmatter",
                points_deducted=self.max_points,
            )]
        return []


class FM006_DescriptionLength(BaseRule):
    rule_id = "FM-006"
    description = "description should be under 1024 chars"
    category = "Frontmatter"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if skill_data.description and len(skill_data.description) >= 1024:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Description is {len(skill_data.description)} chars (max 1024)",
                fix_hint="Shorten description or move details to body",
                points_deducted=self.max_points,
            )]
        return []


class FM007_DescriptionNotEmpty(BaseRule):
    rule_id = "FM-007"
    description = "description must not be empty"
    category = "Frontmatter"
    severity = Severity.ERROR
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if skill_data.description is not None and not skill_data.description.strip():
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Description field is empty or whitespace-only",
                fix_hint="Write a meaningful description that explains when to trigger this skill",
                points_deducted=self.max_points,
            )]
        return []


class FM008_AllowedToolsFormat(BaseRule):
    rule_id = "FM-008"
    description = "allowed-tools should be a list of strings"
    category = "Frontmatter"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        tools = skill_data.allowed_tools
        if tools is None:
            return []
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="allowed-tools should be a list of strings",
                fix_hint="Use format: allowed-tools: [Read, Write, Bash]",
                points_deducted=self.max_points,
            )]
        return []


ALL_RULES = [
    FM001_NameExists(),
    FM002_NameKebabCase(),
    FM003_NameLength(),
    FM004_NameMatchesDir(),
    FM005_DescriptionExists(),
    FM006_DescriptionLength(),
    FM007_DescriptionNotEmpty(),
    FM008_AllowedToolsFormat(),
]
