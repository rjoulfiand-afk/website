"""X003 – Entri Daftar Isi ≠ Heading Aktual (TOC Entry != Actual Heading)."""

from __future__ import annotations

import re
from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


def _clean_text(s: str) -> str:
    """Normalize text for comparison: remove extra whitespace and punctuation."""
    s = re.sub(r"[^\w\s]", "", s)
    return " ".join(s.lower().split())


class X003TOCVsHeadings(BaseRule):
    rule_id = "X003"
    rule_name = "Entri Daftar Isi ≠ Heading Aktual"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        if not ir.toc.entries:
            return findings

        # Clean all actual heading texts
        actual_headings_cleaned = [_clean_text(h.text) for h in ir.headings if h.text.strip()]

        for entry in ir.toc.entries:
            entry_clean = _clean_text(entry.text)
            if not entry_clean:
                continue

            # Check if entry_clean matches or is substring of any actual heading
            matched = any(
                entry_clean == ah or entry_clean in ah or ah in entry_clean
                for ah in actual_headings_cleaned
            )

            if not matched:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.ERROR,
                        confidence=0.92,
                        location=Location(
                            type=LocationType.DOCUMENT,
                            id="toc_entry",
                            label=f"Daftar Isi: '{entry.text}'",
                        ),
                        evidence=Evidence(
                            snippet=entry.text,
                            detail=f"Teks Daftar Isi '{entry.text}' tidak cocok dengan heading aktif dalam dokumen",
                        ),
                        auto_fixable=True,
                        suggestion=(
                            "Perbarui field Daftar Isi (klik kanan pada Daftar Isi > Update Field > Update Entire Table) "
                            "agar judul bab dan sub-bab sesuai dengan isi naskah terbaru."
                        ),
                        guide_module_slug="word-toc",
                    )
                )

        return findings
