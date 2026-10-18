"""Base class for all Rapikan Auto-Fixers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from docx import Document
from rapikan.ir.finding_schema import Finding


class BaseFixer(ABC):
    """Abstract base class for rule-specific automated fixers."""

    rule_id: str = ""

    @abstractmethod
    def fix(self, doc: Document, finding: Finding) -> bool:
        """Apply the safe fix directly into the python-docx Document object.
        
        Returns True if a modification was made, False otherwise.
        """
        ...
