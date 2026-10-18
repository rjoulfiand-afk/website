"""W007 – Gambar atau Tabel Tanpa Keterangan (Caption Missing)."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W007CaptionMissing(BaseRule):
    rule_id = "W007"
    rule_name = "Gambar/Tabel Tanpa Caption"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        # Check tables without captions
        table_captions = [c for c in ir.captions if c.label.lower() in ("tabel", "table")]
        for idx, table in enumerate(ir.tables):
            has_caption = bool(table.caption) or (idx < len(table_captions))
            if not has_caption:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.85,
                        location=Location(
                            type=LocationType.TABLE,
                            id=table.id,
                            label=f"Tabel {table.id}",
                            section_index=table.section_index,
                        ),
                        evidence=Evidence(
                            snippet=f"Tabel {table.id} tidak memiliki caption yang terdeteksi",
                            detail=f"Baris: {len(table.rows)}, Kolom: {len(table.rows[0].cells) if table.rows else 0}",
                        ),
                        auto_fixable=False,
                        suggestion=(
                            "Tambahkan judul/keterangan tabel (caption) menggunakan fitur "
                            "Insert Caption di Microsoft Word dengan format 'Tabel X.X Judul'."
                        ),
                        guide_module_slug="word-caption",
                    )
                )

        return findings
