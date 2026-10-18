"""B002 Fixer: Replaces approved non-standard Indonesian words with KBBI equivalents.

Non-negotiable Invariant:
Only applies to specific approved rewrite proposals, preserving casing and exact word boundaries.
"""

from __future__ import annotations

import re
from docx import Document
from rapikan.fixer.base import BaseFixer
from rapikan.ir.finding_schema import Finding
from rapikan.rules.word.B002_common_typos import EXPLICIT_TYPO_MAP, _match_casing


class B002TypoFixer(BaseFixer):
    rule_id = "B002"

    def fix(self, doc: Document, finding: Finding) -> bool:
        para_id = finding.location.id
        m = re.search(r"p_(\d+)", para_id)
        if not m:
            return False

        para_idx = int(m.group(1)) - 1
        if para_idx < 0 or para_idx >= len(doc.paragraphs):
            return False

        para = doc.paragraphs[para_idx]
        modified = False

        # Extract specific target word and replacement from evidence
        from_word = finding.evidence.extra.get("from_word") if finding.evidence.extra else None
        to_word = finding.evidence.extra.get("to_word") if finding.evidence.extra else None

        if not from_word or not to_word:
            m_detail = re.search(r"Kata tidak baku: '([^']+)' -> '([^']+)'", finding.evidence.detail or "")
            if m_detail:
                from_word = m_detail.group(1)
                to_word = m_detail.group(2)

        if not from_word:
            return False

        pattern = re.compile(rf"\b{re.escape(from_word)}\b", re.IGNORECASE)

        for run in para.runs:
            if pattern.search(run.text):
                def _sub(match: re.Match) -> str:
                    nonlocal modified
                    modified = True
                    return _match_casing(match.group(0), to_word or EXPLICIT_TYPO_MAP.get(from_word.lower(), match.group(0)))

                run.text = pattern.sub(_sub, run.text)

        # Fallback to paragraph text if runs split across boundaries
        if not modified and pattern.search(para.text):
            def _sub_p(match: re.Match) -> str:
                nonlocal modified
                modified = True
                return _match_casing(match.group(0), to_word or EXPLICIT_TYPO_MAP.get(from_word.lower(), match.group(0)))

            para.text = pattern.sub(_sub_p, para.text)

        return modified
