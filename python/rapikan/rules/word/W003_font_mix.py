"""W003 – Mixed font/size within paragraph.

Flags paragraphs where runs have inconsistent font names or sizes,
indicating manual mixed formatting.
"""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile

# Tolerance for font size comparison (in pt)
_SIZE_TOLERANCE_PT = 0.5


class W003FontMix(BaseRule):
    rule_id = "W003"
    rule_name = "Mixed font/size within paragraph"
    phase = 1

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        for para in ir.paragraphs:
            runs = [r for r in para.runs if r.text.strip()]
            if len(runs) < 2:
                continue

            font_names = set()
            font_sizes = set()

            for run in runs:
                es = run.effective_style
                if es.font_name:
                    font_names.add(es.font_name)
                if es.font_size_pt is not None:
                    # Bucket sizes within tolerance
                    bucketed = round(es.font_size_pt / _SIZE_TOLERANCE_PT) * _SIZE_TOLERANCE_PT
                    font_sizes.add(bucketed)

            if len(font_names) > 1 or len(font_sizes) > 1:
                detail_parts = []
                if len(font_names) > 1:
                    detail_parts.append(f"Font names: {sorted(font_names)}")
                if len(font_sizes) > 1:
                    detail_parts.append(f"Font sizes: {sorted(font_sizes)}pt")

                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.90,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=para.id,
                            label=f"Paragraf {para.id}",
                            section_index=para.section_index,
                        ),
                        evidence=Evidence(
                            snippet=para.text[:120],
                            detail="; ".join(detail_parts),
                        ),
                        auto_fixable=True,
                        suggestion=(
                            "Pastikan semua teks dalam paragraf menggunakan "
                            "font dan ukuran yang seragam sesuai panduan penulisan."
                        ),
                        guide_module_slug="w003-font-mix",
                    )
                )

        return findings
