"""Base classes for the rule system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skill_lint.parser import SkillData


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleDiagnostic:
    rule_id: str
    severity: Severity
    message: str
    fix_hint: str = ""
    line: int | None = None
    points_deducted: float = 0


class BaseRule(ABC):
    rule_id: str
    description: str
    category: str
    severity: Severity
    max_points: float = 0

    @abstractmethod
    def check(self, skill_data: SkillData) -> list[RuleDiagnostic]:
        ...
