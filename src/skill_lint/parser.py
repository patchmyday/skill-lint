"""SKILL.md parser: extracts YAML frontmatter and body content."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SkillData:
    """Parsed representation of a SKILL.md file and its surrounding directory."""

    name: str | None = None
    description: str | None = None
    license: str | None = None
    compatibility: str | None = None
    metadata: dict = field(default_factory=dict)
    allowed_tools: list[str] | None = None

    body_text: str = ""
    body_lines: list[str] = field(default_factory=list)

    skill_path: Path = field(default_factory=lambda: Path("."))
    has_scripts: bool = False
    has_references: bool = False
    has_agents: bool = False
    has_assets: bool = False
    has_evals: bool = False

    script_files: list[str] = field(default_factory=list)
    reference_files: list[str] = field(default_factory=list)

    # Raw frontmatter for rules that need it
    raw_frontmatter: dict = field(default_factory=dict)

    # Parse errors
    parse_errors: list[str] = field(default_factory=list)


def parse_skill(skill_dir: str | Path) -> SkillData:
    """Parse a skill directory, reading SKILL.md and scanning the directory structure."""
    skill_dir = Path(skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"

    data = SkillData(skill_path=skill_dir)

    if not skill_md.exists():
        data.parse_errors.append("SKILL.md not found")
        return data

    text = skill_md.read_text(encoding="utf-8")

    # Split frontmatter and body
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if fm_match:
        fm_text, body = fm_match.group(1), fm_match.group(2)
        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError as e:
            data.parse_errors.append(f"YAML parse error: {e}")
            fm = {}
        data.raw_frontmatter = fm
        data.name = fm.get("name")
        data.description = fm.get("description")
        data.license = fm.get("license")
        data.compatibility = fm.get("compatibility")
        data.allowed_tools = fm.get("allowed-tools") or fm.get("allowed_tools")
        # Everything else goes into metadata
        known_keys = {"name", "description", "license", "compatibility", "allowed-tools", "allowed_tools"}
        data.metadata = {k: v for k, v in fm.items() if k not in known_keys}
    else:
        # No frontmatter
        body = text
        data.parse_errors.append("No YAML frontmatter found (missing --- markers)")

    data.body_text = body.strip()
    data.body_lines = body.splitlines()

    # Scan directory structure
    _scan_directory(skill_dir, data)

    return data


def _scan_directory(skill_dir: Path, data: SkillData) -> None:
    """Scan the skill directory for known subdirectories and files."""
    scripts_dir = skill_dir / "scripts"
    refs_dir = skill_dir / "references"
    agents_dir = skill_dir / "agents"
    assets_dir = skill_dir / "assets"
    evals_dir = skill_dir / "evals"

    data.has_scripts = scripts_dir.is_dir()
    data.has_references = refs_dir.is_dir()
    data.has_agents = agents_dir.is_dir()
    data.has_assets = assets_dir.is_dir()
    data.has_evals = evals_dir.is_dir()

    if data.has_scripts:
        data.script_files = [
            f.name for f in scripts_dir.iterdir() if f.is_file()
        ]

    if data.has_references:
        data.reference_files = [
            f.name for f in refs_dir.iterdir() if f.is_file()
        ]
