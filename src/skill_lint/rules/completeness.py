"""Completeness rules (COMP-001 through COMP-009)."""

from __future__ import annotations

import re

from skill_lint.parser import SkillData
from skill_lint.rules.base import BaseRule, RuleDiagnostic, Severity

KNOWN_DIRS = {"scripts", "references", "agents", "assets", "evals", "docs", ".git"}
KNOWN_FILES = {"SKILL.md", "LICENSE", "LICENSE.txt", "LICENSE.md", "README.md", "CLAUDE.md"}


class COMP001_SkillMdExists(BaseRule):
    rule_id = "COMP-001"
    description = "SKILL.md must exist"
    category = "Completeness"
    severity = Severity.ERROR
    max_points = 5

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if "SKILL.md not found" in skill_data.parse_errors:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="SKILL.md not found in skill directory",
                fix_hint="Create a SKILL.md file with frontmatter and instructions",
                points_deducted=self.max_points,
            )]
        return []


class COMP002_ScriptsDirIfNeeded(BaseRule):
    rule_id = "COMP-002"
    description = "scripts/ dir should exist if body mentions running scripts"
    category = "Completeness"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        body_lower = skill_data.body_text.lower()
        mentions_scripts = any(p in body_lower for p in ["run the script", "execute the script", "scripts/"])
        if mentions_scripts and not skill_data.has_scripts:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Body mentions scripts but no scripts/ directory exists",
                fix_hint="Create a scripts/ directory with the referenced scripts",
                points_deducted=self.max_points,
            )]
        return []


class COMP003_ReferencesDirIfNeeded(BaseRule):
    rule_id = "COMP-003"
    description = "references/ dir should exist if body mentions references"
    category = "Completeness"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.body_text:
            return []
        body_lower = skill_data.body_text.lower()
        mentions_refs = any(p in body_lower for p in [
            "see reference", "references/", "refer to", "see the reference",
            "detailed in reference", "reference document",
        ])
        if mentions_refs and not skill_data.has_references:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Body mentions references but no references/ directory exists",
                fix_hint="Create a references/ directory with the referenced files",
                points_deducted=self.max_points,
            )]
        return []


class COMP004_HasEvals(BaseRule):
    rule_id = "COMP-004"
    description = "evals/ directory present (bonus)"
    category = "Completeness"
    severity = Severity.INFO
    max_points = 0

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if skill_data.has_evals:
            return [RuleDiagnostic(
                rule_id="BONUS-COMP004",
                severity=Severity.INFO,
                message="Has evals/ directory — enables automated quality testing",
                points_deducted=-2,
            )]
        return []


class COMP005_HasLicense(BaseRule):
    rule_id = "COMP-005"
    description = "should have LICENSE file or license in frontmatter"
    category = "Completeness"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        has_license_file = any(
            (skill_data.skill_path / f).exists()
            for f in ["LICENSE", "LICENSE.txt", "LICENSE.md"]
        )
        has_license_field = bool(skill_data.license)
        if not has_license_file and not has_license_field:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="No license found (file or frontmatter field)",
                fix_hint="Add a LICENSE file or 'license:' field to frontmatter",
                points_deducted=self.max_points,
            )]
        return []


class COMP006_HasVersion(BaseRule):
    rule_id = "COMP-006"
    description = "version in metadata (info)"
    category = "Completeness"
    severity = Severity.INFO
    max_points = 0

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if "version" in skill_data.metadata or "version" in skill_data.raw_frontmatter:
            return [RuleDiagnostic(
                rule_id="BONUS-COMP006",
                severity=Severity.INFO,
                message="Has version field in metadata",
                points_deducted=-0.5,
            )]
        return []


class COMP007_CompatibilityField(BaseRule):
    rule_id = "COMP-007"
    description = "compatibility field if scripts require specific tools"
    category = "Completeness"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_scripts:
            return []
        if not skill_data.compatibility:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message="Has scripts but no compatibility field in frontmatter",
                fix_hint="Add 'compatibility:' to specify required tools/platforms",
                points_deducted=self.max_points,
            )]
        return []


class COMP008_DirMatchesName(BaseRule):
    rule_id = "COMP-008"
    description = "directory name should match skill name"
    category = "Completeness"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        # Delegated to FM-004, avoid double-counting
        return []


class COMP009_NoUnexpectedFiles(BaseRule):
    rule_id = "COMP-009"
    description = "no unexpected files in skill root"
    category = "Completeness"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        unexpected = []
        try:
            for entry in skill_data.skill_path.iterdir():
                name = entry.name
                if entry.is_dir():
                    if name not in KNOWN_DIRS and not name.startswith("."):
                        unexpected.append(name + "/")
                elif name not in KNOWN_FILES and not name.startswith("."):
                    unexpected.append(name)
        except OSError:
            return []

        if unexpected:
            return [RuleDiagnostic(
                rule_id=self.rule_id, severity=self.severity,
                message=f"Unexpected files/dirs in skill root: {', '.join(unexpected[:5])}",
                fix_hint="Move to scripts/, references/, or assets/ as appropriate",
                points_deducted=min(1, len(unexpected) * 0.25),
            )]
        return []


ALL_RULES = [
    COMP001_SkillMdExists(),
    COMP002_ScriptsDirIfNeeded(),
    COMP003_ReferencesDirIfNeeded(),
    COMP004_HasEvals(),
    COMP005_HasLicense(),
    COMP006_HasVersion(),
    COMP007_CompatibilityField(),
    COMP008_DirMatchesName(),
    COMP009_NoUnexpectedFiles(),
]
