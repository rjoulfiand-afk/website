"""W001 – Fake Heading detection.

A paragraph styled as "Normal" (or equivalent) but with bold text and a
font size >= profile.fake_heading_min_size_pt is flagged as a fake heading.
"""

from __future__ import annotations

from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
from rapikan.ir.schema import IRDocument
from rapikan.rules.base import BaseRule
from rapikan.rules.campus_profile import CampusProfile

# Style names that are proper heading styles (case-insensitive prefix)
_HEADING_PREFIXES = ("heading", "judul", "toc")


def _is_heading_style(style_name: str) -> bool:
    lower = style_name.lower()
    return any(lower.startswith(p) for p in _HEADING_PREFIXES)


class W001FakeHeading(BaseRule):
    rule_id = "W001"
    rule_name = "Fake Heading (Bold+Large with Normal style)"
    phase = 1
    requires_render = False
    requires_llm = False

    def check(self, ir: IRDocument, profile: CampusProfile) -> list[Finding]:
        findings: list[Finding] = []
        threshold = profile.fake_heading_min_size_pt

        for para in ir.paragraphs:
            # Skip proper heading styles
            if _is_heading_style(para.style_name):
                continue

            text = para.text.strip()
            if not text:
                continue

            es = para.effective_style
            is_bold = es.bold is True
            size_pt = es.font_size_pt or 0.0

            # Also check run-level formatting if runs exist
            non_empty_runs = [r for r in para.runs if r.text.strip()]
            if non_empty_runs and (not is_bold or size_pt < threshold):
                runs_bold = all(r.effective_style.bold is True for r in non_empty_runs)
                run_sizes = [r.effective_style.font_size_pt or 0.0 for r in non_empty_runs]
                max_run_size = max(run_sizes) if run_sizes else 0.0
                if runs_bold and max_run_size >= threshold:
                    is_bold = True
                    size_pt = max_run_size

            if is_bold and size_pt >= threshold:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=Severity.WARNING,
                        confidence=0.85,
                        location=Location(
                            type=LocationType.PARAGRAPH,
                            id=para.id,
                            label=f"Paragraf {para.id}",
                            section_index=para.section_index,
                        ),
                        evidence=Evidence(
                            snippet=para.text[:120],
                            detail=(
                                f"Style='{para.style_name}', bold=True, "
                                f"font_size={size_pt}pt (threshold={threshold}pt)"
                            ),
                        ),
                        auto_fixable=True,
                        suggestion=(
                            "Gunakan style Heading yang sesuai (mis. Heading 1, Heading 2) "
                            "daripada memformat manual dengan Bold + ukuran font besar."
                        ),
                        guide_module_slug="w001-fake-heading",
                    )
                )

        return findings
