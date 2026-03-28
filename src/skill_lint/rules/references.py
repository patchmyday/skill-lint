"""Reference and script integrity rules (REF-001 through REF-009)."""

from __future__ import annotations

import os
import re
import stat

from skill_lint.parser import SkillData
from skill_lint.rules.base import BaseRule, RuleDiagnostic, Severity


def _body_referenced_paths(body: str, prefix: str) -> list[str]:
    """Extract paths like scripts/foo.sh or references/bar.md from body text."""
    pattern = rf"{prefix}/[\w./-]+"
    raw = re.findall(pattern, body)
    # Strip trailing punctuation that isn't part of the path
    return [p.rstrip(".,;:!?)") for p in raw]


class REF001_ScriptsExist(BaseRule):
    rule_id = "REF-001"
    description = "scripts referenced in body must exist"
    category = "References"
    severity = Severity.ERROR
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        refs = _body_referenced_paths(skill_data.body_text, "scripts")
        results = []
        for ref in refs:
            full = skill_data.skill_path / ref
            if not full.exists():
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Referenced script '{ref}' does not exist",
                    fix_hint=f"Create {ref} or fix the reference",
                    points_deducted=1.5,
                ))
        return results


class REF002_ReferencesExist(BaseRule):
    rule_id = "REF-002"
    description = "references mentioned in body must exist"
    category = "References"
    severity = Severity.ERROR
    max_points = 3

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        refs = _body_referenced_paths(skill_data.body_text, "references")
        results = []
        for ref in refs:
            full = skill_data.skill_path / ref
            if not full.exists():
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Referenced file '{ref}' does not exist",
                    fix_hint=f"Create {ref} or fix the reference",
                    points_deducted=1.5,
                ))
        return results


class REF003_ScriptsExecutable(BaseRule):
    rule_id = "REF-003"
    description = "scripts should be executable"
    category = "References"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_scripts:
            return []
        results = []
        scripts_dir = skill_data.skill_path / "scripts"
        for f in scripts_dir.iterdir():
            if f.is_file() and not (f.stat().st_mode & stat.S_IXUSR):
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Script '{f.name}' is not executable",
                    fix_hint=f"Run: chmod +x scripts/{f.name}",
                    points_deducted=0.5,
                ))
        return results


class REF004_NoOrphanScripts(BaseRule):
    rule_id = "REF-004"
    description = "scripts/ files should be mentioned in body"
    category = "References"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_scripts:
            return []
        results = []
        for sf in skill_data.script_files:
            if sf not in skill_data.body_text:
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Script '{sf}' not referenced in SKILL.md body",
                    fix_hint=f"Reference scripts/{sf} in the body or remove it",
                    points_deducted=0.5,
                ))
        return results


class REF005_NoOrphanReferences(BaseRule):
    rule_id = "REF-005"
    description = "references/ files should be mentioned in body"
    category = "References"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_references:
            return []
        results = []
        for rf in skill_data.reference_files:
            if rf not in skill_data.body_text:
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Reference '{rf}' not referenced in SKILL.md body",
                    fix_hint=f"Reference references/{rf} in the body or remove it",
                    points_deducted=0.5,
                ))
        return results


class REF006_WikiLinks(BaseRule):
    rule_id = "REF-006"
    description = "WikiLink targets should exist"
    category = "References"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        links = re.findall(r"\[\[([^\]]+)\]\]", skill_data.body_text)
        results = []
        for link in links:
            # Check common locations
            found = False
            for subdir in ["references", "scripts", ""]:
                candidate = skill_data.skill_path / subdir / link if subdir else skill_data.skill_path / link
                if candidate.exists():
                    found = True
                    break
                # Try with .md extension
                if not link.endswith(".md"):
                    candidate_md = skill_data.skill_path / subdir / f"{link}.md" if subdir else skill_data.skill_path / f"{link}.md"
                    if candidate_md.exists():
                        found = True
                        break
            if not found:
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"WikiLink target '[[{link}]]' not found",
                    fix_hint=f"Create the linked file or fix the WikiLink",
                    points_deducted=0.5,
                ))
        return results


class REF007_ForwardSlashes(BaseRule):
    rule_id = "REF-007"
    description = "referenced paths should use forward slashes"
    category = "References"
    severity = Severity.WARNING
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if "\\" in skill_data.body_text:
            # Check if backslashes are in path-like contexts
            backslash_paths = re.findall(r"[\w]+\\[\w]+", skill_data.body_text)
            if backslash_paths:
                return [RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message="Backslashes found in paths — use forward slashes",
                    fix_hint="Replace \\ with / in file paths",
                    points_deducted=self.max_points,
                )]
        return []


class REF008_ScriptShebangs(BaseRule):
    rule_id = "REF-008"
    description = "scripts should have shebangs"
    category = "References"
    severity = Severity.WARNING
    max_points = 2

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_scripts:
            return []
        results = []
        scripts_dir = skill_data.skill_path / "scripts"
        for f in scripts_dir.iterdir():
            if not f.is_file():
                continue
            # Skip non-script files (e.g., .json, .yaml)
            if f.suffix in (".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".csv"):
                continue
            try:
                first_line = f.read_text(encoding="utf-8").split("\n", 1)[0]
                if not first_line.startswith("#!"):
                    results.append(RuleDiagnostic(
                        rule_id=self.rule_id, severity=self.severity,
                        message=f"Script '{f.name}' has no shebang line",
                        fix_hint=f"Add #!/usr/bin/env python3 (or bash) to scripts/{f.name}",
                        points_deducted=0.5,
                    ))
            except (UnicodeDecodeError, OSError):
                pass
        return results


class REF009_ReferenceMarkdown(BaseRule):
    rule_id = "REF-009"
    description = "reference files should be markdown"
    category = "References"
    severity = Severity.INFO
    max_points = 1

    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        if not skill_data.has_references:
            return []
        results = []
        for rf in skill_data.reference_files:
            if not rf.endswith(".md"):
                results.append(RuleDiagnostic(
                    rule_id=self.rule_id, severity=self.severity,
                    message=f"Reference '{rf}' is not a markdown file",
                    fix_hint="Reference files should typically be .md for best LLM consumption",
                    points_deducted=0.25,
                ))
        return results


ALL_RULES = [
    REF001_ScriptsExist(),
    REF002_ReferencesExist(),
    REF003_ScriptsExecutable(),
    REF004_NoOrphanScripts(),
    REF005_NoOrphanReferences(),
    REF006_WikiLinks(),
    REF007_ForwardSlashes(),
    REF008_ScriptShebangs(),
    REF009_ReferenceMarkdown(),
]
