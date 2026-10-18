"""W002 – Manual Numbering.

Detects paragraphs that use manually typed numbering (e.g. "1.", "a.", "(1)")
instead of Word's automatic list styles.
"""

from __future__ import annotations

import re

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class W002ManualNumbering(BaseRule):
    rule_id = "W002"
    rule_name = "Manual Numbering (typed list numbers)"
    phase = 1

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []
        patterns = [re.compile(p) for p in profile.manual_numbering_patterns]

        for para in ir.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            # Skip paragraphs that are already list-styled
            style_lower = para.style_name.lower()
            if "list" in style_lower:
                continue

            for pattern in patterns:
                if pattern.match(text):
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            severity=Severity.WARNING,
                            confidence=0.80,
                            location=Location(
                                type=LocationType.PARAGRAPH,
                                id=para.id,
                                label=f"Paragraf {para.id}",
                                section_index=para.section_index,
                            ),
                            evidence=Evidence(
                                snippet=text[:120],
                                detail=f"Terdeteksi pola penomoran manual: '{pattern.pattern}'",
                            ),
                            auto_fixable=False,
                            suggestion=(
                                "Gunakan fitur List/Numbering otomatis Word "
                                "daripada mengetik nomor secara manual."
                            ),
                            guide_module_slug="w002-manual-numbering",
                        )
                    )
                    break  # one finding per paragraph

        return findings
