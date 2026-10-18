"""X001 – Sitasi Tanpa Entri di Daftar Pustaka (Citation Missing in Bibliography)."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class X001CitationVsBib(BaseRule):
    rule_id = "X001"
    rule_name = "Sitasi Tanpa Entri di Daftar Pustaka"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        # Build list of normalized bib keys
        bib_keys = [b.key.lower() for b in ir.bib_entries]
        bib_texts = [b.raw_text.lower() for b in ir.bib_entries]

        for cite in ir.inline_citations:
            cite_key = cite.key.lower()
            # Check if citation key matches any bib key or appears in bib text
            matched = any(
                cite_key in bk or bk in cite_key or cite_key in bt
                for bk, bt in zip(bib_keys, bib_texts)
            )

            if not matched:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.ERROR,
                        confidence=0.90,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=cite.paragraph_id,
                            label=f"Sitasi pada paragraf {cite.paragraph_id}",
                        ),
                        evidence=Evidence(
                            snippet=cite.raw_text,
                            detail=f"Kunci sitasi '{cite.key}' tidak ditemukan pada {len(ir.bib_entries)} entri Daftar Pustaka",
                        ),
                        auto_fixable=False,
                        suggestion=(
                            f"Tambahkan rujukan lengkap untuk sitasi '{cite.raw_text}' "
                            "ke dalam bagian Daftar Pustaka sesuai gaya sitasi yang ditentukan."
                        ),
                        guide_module_slug="word-citation",
                    )
                )

        return findings
