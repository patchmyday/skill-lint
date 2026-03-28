"""Tests for the SKILL.md parser."""

from skill_lint.parser import parse_skill


def test_parse_perfect_skill(perfect_skill_dir):
    data = parse_skill(perfect_skill_dir)
    assert data.name == "perfect-skill"
    assert "CSV" in data.description
    assert data.license == "MIT"
    assert data.has_scripts is True
    assert data.has_references is True
    assert "validate.sh" in data.script_files
    assert "ADVANCED.md" in data.reference_files
    assert len(data.body_lines) > 5
    assert not data.parse_errors


def test_parse_minimal_skill(minimal_skill_dir):
    data = parse_skill(minimal_skill_dir)
    assert data.name == "minimal-skill"
    assert data.description is not None
    assert data.has_scripts is False
    assert data.has_references is False


def test_parse_broken_skill(broken_skill_dir):
    data = parse_skill(broken_skill_dir)
    assert data.name is None  # missing name field
    assert data.description == "helps with stuff"
    assert data.has_scripts is True
    assert data.has_references is True


def test_parse_missing_dir(tmp_path):
    data = parse_skill(tmp_path / "nonexistent")
    assert "SKILL.md not found" in data.parse_errors


def test_parse_no_frontmatter(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Just a heading\n\nSome body text.\n")
    data = parse_skill(tmp_path)
    assert data.name is None
    assert "No YAML frontmatter found" in data.parse_errors[0]
    assert "Just a heading" in data.body_text
