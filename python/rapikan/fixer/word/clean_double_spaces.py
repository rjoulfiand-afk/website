r"""W010 Fixer: Cleans double and multiple consecutive spaces in paragraphs.

Invariant:
Hash teks setelah normalisasi whitespace (re.sub(r'\s+', ' ', text).strip())
WAJIB identik sebelum dan sesudah perbaikan spasi ganda.
"""

from __future__ import annotations

import hashlib
import re
from docx import Document
from rapikan.fixer.base import BaseFixer
from rapikan.ir.finding_schema import Finding


def _norm_hash(text: str) -> str:
    norm = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class W010DoubleSpaceFixer(BaseFixer):
    rule_id = "W010"

    def fix(self, doc: Document, finding: Finding) -> bool:
        para_id = finding.location.id
        m = re.search(r"p_(\d+)", para_id)
        if not m:
            return False

        para_idx = int(m.group(1)) - 1
        if para_idx < 0 or para_idx >= len(doc.paragraphs):
            return False

        para = doc.paragraphs[para_idx]

        # Guard against touching alignment lines (e.g. "Nama      : Budi")
        if re.search(r"[ ]{2,}:", para.text):
            return False

        hash_before = _norm_hash(para.text)
        modified = False

        prose_double_re = re.compile(r"(?<=[a-zA-Z0-9,\.\?!;'\"])[ ]{2,}(?=[a-zA-Z0-9'\"\(])")

        for run in para.runs:
            if prose_double_re.search(run.text):
                new_text = prose_double_re.sub(" ", run.text)
                if new_text != run.text:
                    run.text = new_text
                    modified = True

        # Check whole paragraph if runs didn't catch boundary double spaces
        if prose_double_re.search(para.text):
            new_text = prose_double_re.sub(" ", para.text)
            para.text = new_text
            modified = True

        # Verify invariant: Normalized whitespace text MUST be identical
        hash_after = _norm_hash(para.text)
        if hash_before != hash_after:
            raise ValueError(
                f"Violasi Invarian W010: Normalisasi whitespace menghasilkan teks yang tidak identik! "
                f"Sebelum ({hash_before}) vs Sesudah ({hash_after})"
            )

        return modified
