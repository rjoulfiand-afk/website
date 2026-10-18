"""W012 – Urutan Bab Tidak Sesuai Profil (Chapter Order Violation)."""

from __future__ import annotations

import re
from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W012ChapterOrder(BaseRule):
    rule_id = "W012"
    rule_name = "Urutan Bab Tidak Sesuai Profil"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []
        expected_chapters = profile.chapter_order.chapters

        # Extract normalized headings that match expected chapters
        matched_headings = []
        for h in ir.headings:
            text_upper = h.text.strip().upper()
            for exp_idx, exp_ch in enumerate(expected_chapters):
                # Match word boundary e.g. "BAB I", "DAFTAR ISI", "BAB II"
                pattern = rf"\b{re.escape(exp_ch)}\b"
                if re.search(pattern, text_upper):
                    matched_headings.append((exp_idx, exp_ch, h))
                    break

        # Check for non-decreasing order of expected indices
        last_index = -1
        for exp_idx, exp_ch, h in matched_headings:
            if exp_idx < last_index:
                # Out of order!
                prev_name = expected_chapters[last_index]
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.ERROR,
                        confidence=0.95,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=h.id,
                            label=f"Heading {h.id} ({h.text[:40]})",
                            section_index=h.section_index,
                        ),
                        evidence=Evidence(
                            snippet=h.text[:100],
                            detail=f"Bagian/Bab '{exp_ch}' (urutan {exp_idx + 1}) muncul setelah '{prev_name}' (urutan {last_index + 1}) pada naskah bergenre '{profile.genre}'.",
                        ),
                        auto_fixable=False,
                        suggestion=(
                            f"Sesuaikan susunan bagian/bab agar berurutan sesuai pedoman penulisan ({profile.genre}): '{exp_ch}' "
                            f"seharusnya berada sebelum '{prev_name}'."
                        ),
                        guide_module_slug="word-chapter-structure",
                    )
                )
            else:
                last_index = exp_idx

        return findings
