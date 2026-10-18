"""X004 – Nomor Gambar/Tabel Tidak Berurutan (Sequence Numbering Gaps)."""

from __future__ import annotations

from collections import defaultdict
from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile


class X004NumberingSequence(BaseRule):
    rule_id = "X004"
    rule_name = "Nomor Gambar/Tabel Tidak Berurutan"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []

        # Group captions by label and chapter
        groups: dict[tuple[str, int | None], list] = defaultdict(list)
        for cap in ir.captions:
            if cap.number is not None:
                groups[(cap.label.lower(), cap.chapter)].append(cap)

        for (label, chapter), cap_list in groups.items():
            expected_num = 1
            for cap in cap_list:
                if cap.number != expected_num:
                    ch_str = f" Bab {chapter}" if chapter is not None else ""
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            severity=Severity.ERROR,
                            confidence=0.92,
                            location=Location(
                                type=LocationType.PARAGRAPH,
                                id=cap.id,
                                label=f"Caption {cap.label}{ch_str} ({cap.id})",
                            ),
                            evidence=Evidence(
                                snippet=cap.full_text,
                                detail=f"Ditemukan nomor {cap.number}, seharusnya nomor {expected_num}",
                            ),
                            auto_fixable=True,
                            suggestion=(
                                f"Perbaiki penomoran urut {cap.label}: setelah nomor {expected_num - 1}, "
                                f"nomor selanjutnya seharusnya adalah {expected_num}."
                            ),
                            guide_module_slug="word-caption",
                        )
                    )
                expected_num = cap.number + 1

        return findings
