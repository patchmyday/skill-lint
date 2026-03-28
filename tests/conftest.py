"""Shared test fixtures."""

from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def perfect_skill_dir():
    return FIXTURES_DIR / "perfect_skill"


@pytest.fixture
def minimal_skill_dir():
    return FIXTURES_DIR / "minimal_skill"


@pytest.fixture
def broken_skill_dir():
    return FIXTURES_DIR / "broken_skill"
