"""W006 – Tabel Tanpa Baris Header Terformat (Table Missing Formatted Header Row)."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W006TableNoHeader(BaseRule):
    rule_id = "W006"
    rule_name = "Tabel Tanpa Baris Header Terformat"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        for table in ir.tables:
            if not table.rows:
                continue

            row_0 = table.rows[0]
            # Check if row 0 is explicitly marked as header or has bold formatting across cells
            is_header_marked = row_0.is_header

            all_cells_bold = False
            if row_0.cells:
                bold_cell_flags = []
                for cell in row_0.cells:
                    cell_is_bold = any(
                        p.effective_style.bold is True or any(r.effective_style.bold is True for r in p.runs)
                        for p in cell.paragraphs
                    )
                    bold_cell_flags.append(cell_is_bold)
                all_cells_bold = all(bold_cell_flags) and len(bold_cell_flags) > 0

            if not (is_header_marked and all_cells_bold):
                cell_previews = [
                    "".join(p.text for p in c.paragraphs)[:30] for c in row_0.cells[:3]
                ]
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
                            snippet=f"Baris 1 tabel: {', '.join(cell_previews)}",
                            detail=f"is_header_marked={is_header_marked}, all_cells_bold={all_cells_bold}",
                        ),
                        auto_fixable=True,
                        suggestion=(
                            "Pastikan baris pertama tabel diformat sebagai header row "
                            "(tebal, aktifkan 'Repeat as header row at the top of each page')."
                        ),
                        guide_module_slug="word-table-format",
                    )
                )

        return findings
