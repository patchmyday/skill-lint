"""Tests for frontmatter rules."""

from pathlib import Path

from skill_lint.parser import SkillData
from skill_lint.rules.frontmatter import (
    FM001_NameExists,
    FM002_NameKebabCase,
    FM003_NameLength,
    FM004_NameMatchesDir,
    FM005_DescriptionExists,
    FM007_DescriptionNotEmpty,
    FM008_AllowedToolsFormat,
)


def _make_skill(**kwargs) -> SkillData:
    defaults = {"skill_path": Path("/fake/my-skill")}
    defaults.update(kwargs)
    return SkillData(**defaults)


def test_fm001_name_missing():
    diags = FM001_NameExists().check(_make_skill(name=None))
    assert len(diags) == 1
    assert diags[0].rule_id == "FM-001"


def test_fm001_name_present():
    diags = FM001_NameExists().check(_make_skill(name="my-skill"))
    assert len(diags) == 0


def test_fm002_kebab_case_valid():
    diags = FM002_NameKebabCase().check(_make_skill(name="my-cool-skill"))
    assert len(diags) == 0


def test_fm002_kebab_case_invalid():
    for bad in ["MySkill", "my_skill", "My-Skill", "SKILL", "my--skill"]:
        diags = FM002_NameKebabCase().check(_make_skill(name=bad))
        assert len(diags) == 1, f"Expected failure for: {bad}"


def test_fm003_name_too_long():
    diags = FM003_NameLength().check(_make_skill(name="a" * 64))
    assert len(diags) == 1


def test_fm003_name_ok():
    diags = FM003_NameLength().check(_make_skill(name="short"))
    assert len(diags) == 0


def test_fm004_name_matches_dir():
    diags = FM004_NameMatchesDir().check(_make_skill(name="my-skill"))
    assert len(diags) == 0


def test_fm004_name_mismatch():
    diags = FM004_NameMatchesDir().check(_make_skill(name="other-name"))
    assert len(diags) == 1


def test_fm005_description_missing():
    diags = FM005_DescriptionExists().check(_make_skill(description=None))
    assert len(diags) == 1


def test_fm007_description_empty():
    diags = FM007_DescriptionNotEmpty().check(_make_skill(description="   "))
    assert len(diags) == 1


def test_fm007_description_ok():
    diags = FM007_DescriptionNotEmpty().check(_make_skill(description="Does stuff"))
    assert len(diags) == 0


def test_fm008_tools_valid():
    diags = FM008_AllowedToolsFormat().check(_make_skill(allowed_tools=["Read", "Write"]))
    assert len(diags) == 0


def test_fm008_tools_invalid():
    diags = FM008_AllowedToolsFormat().check(_make_skill(allowed_tools="Read, Write"))
    assert len(diags) == 1
