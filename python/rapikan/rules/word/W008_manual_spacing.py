"""W008 – Spasi / Enter Manual Antar Paragraf (Manual Spacing / Blank Paragraphs).

Non-negotiable structural guards:
- Paragraf HANYA dianggap kosong jika:
  1. text.strip() kosong
  2. TIDAK mengandung gambar / drawing (w:drawing, w:pict)
  3. TIDAK mengandung persamaan matematika (m:oMath, m:oMathPara)
  4. TIDAK mengandung section break (w:sectPr)
  5. TIDAK mengandung page break (w:br type=page, lastRenderedPageBreak)
  6. TIDAK mengandung fields (PAGE, TOC, SEQ, dll.)
  7. TIDAK mengandung bookmark (w:bookmarkStart)
  8. BUKAN paragraf pemisah di antara dua tabel berurutan
  9. BUKAN paragraf di dalam sel tabel (w:tc)
"""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument, Paragraph
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


def _is_genuinely_blank(p: Paragraph) -> bool:
    """Whitelist approach (Requirement 2): Only genuinely blank paragraphs are flagged."""
    if p.text.strip():
        return False
    if (
        p.has_drawing
        or p.has_math
        or p.has_sect_pr
        or p.has_page_break
        or p.has_fields
        or p.has_bookmark
        or p.has_revisions
        or p.has_comments
        or p.has_sdt
        or p.has_alternate_content
        or p.is_table_separator
        or p.is_in_table_cell
    ):
        return False
    return True


class W008ManualSpacing(BaseRule):
    rule_id = "W008"
    rule_name = "Spasi / Enter Manual Antar Paragraf"
    phase = 1
    requires_render = False
    requires_llm = False
    changes_text = False  # Does not modify manuscript text; only cleans redundant blank separators
    applies_to = ["*"]

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        consecutive_blanks: list[Paragraph] = []

        for p in ir.paragraphs:
            if _is_genuinely_blank(p):
                consecutive_blanks.append(p)
            else:
                if len(consecutive_blanks) >= 2:
                    first = consecutive_blanks[0]
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            severity=Severity.WARNING,
                            confidence=0.90,
                            location=Location(
                                type=LocationType.PARAGRAPH,
                                id=first.id,
                                label=f"Paragraf {first.id}",
                                section_index=first.section_index,
                            ),
                            evidence=Evidence(
                                snippet=f"Terdeteksi {len(consecutive_blanks)} baris kosong berurutan",
                                detail=f"Paragraf ID: {[b.id for b in consecutive_blanks]}",
                            ),
                            auto_fixable=True,
                            suggestion=(
                                "Hapus baris kosong manual (Enter berulang) dan gunakan pengaturan "
                                "Spasi Sebelum/Sesudah Paragraf (Spacing Before/After) pada style paragraf."
                            ),
                            guide_module_slug="word-spacing",
                        )
                    )
                consecutive_blanks = []

        # Check trailing blanks at document end
        if len(consecutive_blanks) >= 2:
            first = consecutive_blanks[0]
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=Severity.WARNING,
                    confidence=0.90,
                    location=Location(
                        type=LocationType.PARAGRAPH,
                        id=first.id,
                        label=f"Paragraf {first.id}",
                        section_index=first.section_index,
                    ),
                    evidence=Evidence(
                        snippet=f"Terdeteksi {len(consecutive_blanks)} baris kosong berurutan di akhir dokumen",
                        detail=f"Paragraf ID: {[b.id for b in consecutive_blanks]}",
                    ),
                    auto_fixable=True,
                    suggestion=(
                        "Hapus baris kosong manual di akhir dokumen dan gunakan pengaturan spasi resmi."
                    ),
                    guide_module_slug="word-spacing",
                )
            )

        return findings
