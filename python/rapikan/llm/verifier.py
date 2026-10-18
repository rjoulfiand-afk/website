"""LLM verifier: verify paragraph_id + quote exist in the IR."""

from __future__ import annotations

from rapikan.ir.schema import IRDocument
from rapikan.llm.client import LLMClient


class LLMVerifier:
    """Uses the LLM to verify and augment findings."""

    def __init__(self, client: LLMClient, ir: IRDocument):
        self._client = client
        self._ir = ir

    def verify_paragraph(self, paragraph_id: str, quote: str) -> bool:
        """Return True if *quote* is found in the paragraph with *paragraph_id*."""
        for para in self._ir.paragraphs:
            if para.id == paragraph_id:
                return quote.lower() in para.text.lower()
        return False
