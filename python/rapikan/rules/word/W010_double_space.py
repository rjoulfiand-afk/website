"""W010 – Spasi Ganda dalam Teks (Double Space in Text)."""

from __future__ import annotations

import re
from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W010DoubleSpace(BaseRule):
    rule_id = "W010"
    rule_name = "Spasi Ganda dalam Teks"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []
        if not profile.check_double_space:
            return findings

        # Prose double space regex (only between words in prose; ignore alignment before colon or code)
        prose_double_space_pattern = re.compile(r"(?<=[a-zA-Z0-9,\.\?!;'\"])[ ]{2,}(?=[a-zA-Z0-9'\"\(])")

        for p in ir.paragraphs:
            text = p.text
            # Skip alignment lines (e.g. "Nama      : Budi", cover page / tabular alignments)
            if re.search(r"[ ]{2,}:", text):
                continue

            match = prose_double_space_pattern.search(text)
            if match:
                # Find start and context
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end]

                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.INFO,
                        confidence=0.99,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=p.id,
                            label=f"Paragraf {p.id}",
                            section_index=p.section_index,
                        ),
                        evidence=Evidence(
                            snippet=f"...{snippet}...",
                            detail=f"Terdeteksi {len(match.group())} spasi berurutan pada posisi karakter {match.start()}",
                        ),
                        auto_fixable=True,
                        suggestion=(
                            "Ganti spasi ganda dengan satu spasi standar untuk menjaga kerapian pengetikan teks."
                        ),
                        guide_module_slug="word-spacing",
                    )
                )

        return findings
