"""W004 – Inconsistent margin/orientation across sections."""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile
from rapikan.utils.twips import twips_approx_equal

_MARGIN_TOLERANCE = 2  # twips


class W004MarginSection(BaseRule):
    rule_id = "W004"
    rule_name = "Inconsistent margin/orientation across sections"
    phase = 1

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []
        sections = ir.sections
        if len(sections) < 2:
            return findings

        # Use first section as baseline
        baseline = sections[0]

        for section in sections[1:]:
            # Check orientation change (landscape in an otherwise portrait doc is OK for appendix)
            if section.orientation != baseline.orientation:
                pass  # orientation changes are acceptable (e.g. wide tables), skip

            # Check margin consistency
            m_base = baseline.margins
            m_curr = section.margins

            margin_issues = []
            for side in ("top", "bottom", "left", "right"):
                base_val = getattr(m_base, f"{side}_twip")
                curr_val = getattr(m_curr, f"{side}_twip")
                if base_val is not None and curr_val is not None:
                    if not twips_approx_equal(base_val, curr_val, _MARGIN_TOLERANCE):
                        margin_issues.append(
                            f"{side}: section 0={base_val}twips vs "
                            f"section {section.index}={curr_val}twips"
                        )

            if margin_issues:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.90,
                        location=Location(
                            type=LocationType.SECTION,
                            id=f"section_{section.index}",
                            label=f"Seksi {section.index}",
                            section_index=section.index,
                        ),
                        evidence=Evidence(
                            snippet=f"Seksi {section.index} margin tidak konsisten",
                            detail="; ".join(margin_issues),
                        ),
                        auto_fixable=False,
                        suggestion=(
                            "Pastikan margin halaman konsisten di seluruh dokumen "
                            "kecuali untuk halaman dengan orientasi landscape."
                        ),
                        guide_module_slug="w004-margin-section",
                    )
                )

        return findings
