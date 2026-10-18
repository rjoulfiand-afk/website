"""X002 – Daftar Pustaka Tidak Disitasi (Bibliography Entry Not Cited in Body)."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class X002BibUncited(BaseRule):
    rule_id = "X002"
    rule_name = "Daftar Pustaka Tidak Disitasi"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        cite_keys = [c.key.lower() for c in ir.inline_citations]
        cite_raws = [c.raw_text.lower() for c in ir.inline_citations]

        for bib in ir.bib_entries:
            bib_key = bib.key.lower()
            # Check if bib entry key is referenced in any inline citation
            is_cited = any(
                bib_key in ck or ck in bib_key or any(part in cr for part in bib_key.split(",") if len(part.strip()) > 3)
                for ck, cr in zip(cite_keys, cite_raws)
            )

            if not is_cited:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.85,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=bib.paragraph_id,
                            label=f"Daftar Pustaka ({bib.paragraph_id})",
                        ),
                        evidence=Evidence(
                            snippet=bib.raw_text[:120],
                            detail=f"Entri rujukan '{bib.key}' tidak ditemukan pada sitasi tubuh naskah",
                        ),
                        auto_fixable=False,
                        suggestion=(
                            "Pastikan setiap rujukan dalam Daftar Pustaka benar-benar disitir dalam naskah, "
                            "atau hapus entri ini jika tidak digunakan."
                        ),
                        guide_module_slug="word-citation",
                    )
                )

        return findings
