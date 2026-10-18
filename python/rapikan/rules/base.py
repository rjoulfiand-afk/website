"""BaseRule ABC for all Rapikan rules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rapikan.ir.finding_schema import Finding
from rapikan.ir.schema import IRDocument
from rapikan.rules.campus_profile import CampusProfile


class BaseRule(ABC):
    """Abstract base class for all Rapikan rules."""

    rule_id: str = ""
    rule_name: str = ""
    phase: int = 1
    requires_render: bool = False
    requires_llm: bool = False
    changes_text: bool = False  # If True, CANNOT run in batch/Rapikan Semua Sekaligus
    applies_to: list[str] = ["*"]  # List of genre IDs or ["*"] for universal

    @abstractmethod
    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        """Run the rule against the IR document and return findings."""
        ...

    def __repr__(self) -> str:
        return f"<Rule {self.rule_id}: {self.rule_name} (changes_text={self.changes_text})>"
