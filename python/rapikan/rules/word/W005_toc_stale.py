"""W005 – Daftar Isi Tidak Otomatis atau Kedaluwarsa (TOC Missing or Not Auto)."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W005TOCStale(BaseRule):
    rule_id = "W005"
    rule_name = "Daftar Isi Tidak Otomatis atau Kedaluwarsa"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        # If document has headings but no auto TOC
        has_headings = len(ir.headings) > 0
        has_auto_toc = ir.toc.is_auto or len(ir.toc.entries) > 0

        if not has_auto_toc:
            toc_loc_id = "doc_toc"
            section_idx = 0
            # Look for manual TOC heading if present
            for p in ir.paragraphs:
                if "daftar isi" in p.text.lower():
                    toc_loc_id = p.id
                    section_idx = p.section_index
                    break

            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=Severity.ERROR,
                    confidence=0.95,
                    location=Location(
                        type=LocationType.PARAGRAPH if toc_loc_id != "doc_toc" else LocationType.DOCUMENT,
                        id=toc_loc_id,
                        label="Daftar Isi",
                        section_index=section_idx,
                    ),
                    evidence=Evidence(
                        snippet="Daftar Isi tidak menggunakan field otomatis (TOC field)",
                        detail=(
                            f"is_auto={ir.toc.is_auto}, "
                            f"jumlah_entri={len(ir.toc.entries)}, "
                            f"jumlah_heading_terdeteksi={len(ir.headings)}"
                        ),
                    ),
                    auto_fixable=True,
                    suggestion=(
                        "Gunakan fitur Daftar Isi (Table of Contents) otomatis Word "
                        "(References > Table of Contents) agar nomor halaman dan judul bab diperbarui secara akurat."
                    ),
                    guide_module_slug="word-toc",
                )
            )

        return findings
