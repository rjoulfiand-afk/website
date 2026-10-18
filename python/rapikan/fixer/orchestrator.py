"""Auto-Fixer Orchestrator for Rapikan.

Non-negotiable Invariants:
1. File asli tidak pernah ditimpa (src_path != out_path).
2. Perubahan style menggunakan style Word semantik, bukan format langsung per run.
3. Teks naskah identik sebelum/sesudah fix (kecuali usulan tulis-ulang yang disetujui satu per satu).
   Aturan dengan changes_text = True (seperti B002) DILARANG berjalan di mode batch.
4. Jika analisis ulang masih menemukan temuan untuk aturan yang diperbaiki, atau muncul
   temuan baru dari aturan lain, lakukan ROLLBACK otomatis: hapus out_path, jangan tandai fixed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from docx import Document

from rapikan.converter.docx_converter import convert_docx
from rapikan.fixer.base import BaseFixer
from rapikan.fixer.word.apply_heading_style import W001HeadingFixer
from rapikan.fixer.word.apply_table_header import W006TableHeaderFixer
from rapikan.fixer.word.remove_blank_paragraphs import W008BlankParagraphFixer
from rapikan.fixer.word.clean_double_spaces import W010DoubleSpaceFixer
from rapikan.fixer.word.replace_typos import B002TypoFixer
from rapikan.ir.finding_schema import Finding
from rapikan.rules.campus_profile import DEFAULT_PROFILE, CampusProfile
from rapikan.rules.word.W001_fake_heading import W001FakeHeading
from rapikan.rules.word.W006_table_no_header import W006TableNoHeader
from rapikan.rules.word.W008_manual_spacing import W008ManualSpacing
from rapikan.rules.word.W010_double_space import W010DoubleSpace
from rapikan.rules.word.B002_common_typos import B002CommonTypos


class RollbackError(Exception):
    """Raised when re-analysis detects residual or new findings, triggering an automatic rollback."""
    pass


class DocumentFixer:
    """Coordinates all automated safe repairs on a Word document with invariant guards."""

    def __init__(self, profile: CampusProfile | None = None):
        self.profile = profile or DEFAULT_PROFILE
        self._fixers: dict[str, BaseFixer] = {
            "W001": W001HeadingFixer(self.profile),
            "W006": W006TableHeaderFixer(),
            "W008": W008BlankParagraphFixer(),
            "W010": W010DoubleSpaceFixer(),
            "B002": B002TypoFixer(),
        }
        self._rule_checkers: dict[str, Any] = {
            "W001": W001FakeHeading(),
            "W006": W006TableNoHeader(),
            "W008": W008ManualSpacing(),
            "W010": W010DoubleSpace(),
            "B002": B002CommonTypos(),
        }

    def register_fixer(self, fixer: BaseFixer, checker: Any | None = None) -> None:
        self._fixers[fixer.rule_id] = fixer
        if checker:
            self._rule_checkers[fixer.rule_id] = checker

    def apply_fixes(
        self,
        src_path: Path,
        out_path: Path,
        findings: list[Finding],
        allow_text_changes: bool = False,
    ) -> dict[str, Any]:
        """Apply safe auto-fixes with mandatory rollback if re-analysis is not clean.
        
        Invariant 1: src_path is NEVER overwritten.
        Invariant 3: Rules with changes_text=True cannot run in batch unless allow_text_changes is True.
        Invariant 4: Automatic rollback if residual or new findings appear.
        """
        src = Path(src_path).resolve()
        out = Path(out_path).resolve()

        if src == out:
            raise ValueError(
                f"Violasi Invarian 1: Berkas asli tidak boleh ditimpa! "
                f"src_path ({src}) sama dengan out_path ({out})."
            )

        if not src.exists():
            raise FileNotFoundError(f"Berkas asli tidak ditemukan: {src}")

        out.parent.mkdir(parents=True, exist_ok=True)

        doc = Document(str(src))
        applied_details = []
        applied_rule_ids = set()

        is_batch = len(findings) > 1

        applied_findings: list[Finding] = []

        for finding in findings:
            # Invariant 3 guard: Text-altering rules CANNOT run in batch
            if finding.changes_text and is_batch and not allow_text_changes:
                continue

            fixer = self._fixers.get(finding.rule_id)
            if not fixer:
                continue

            try:
                success = fixer.fix(doc, finding)
                if success:
                    applied_details.append({
                        "rule_id": finding.rule_id,
                        "location_id": finding.location.id,
                        "suggestion": finding.suggestion,
                        "status": "applied",
                    })
                    applied_rule_ids.add(finding.rule_id)
                    applied_findings.append(finding)
            except Exception as e:
                applied_details.append({
                    "rule_id": finding.rule_id,
                    "location_id": finding.location.id,
                    "status": "error",
                    "error": str(e),
                })

        # Save temporary fixed copy for verification
        doc.save(str(out))

        # Invariant 4: Mandatory Re-analysis and Rollback Guard
        if applied_rule_ids:
            try:
                ir_after = convert_docx(out)
                failed_targeted_findings = []

                # Gather post-fix findings for all rules that were applied
                post_findings_by_rule: dict[str, list[Finding]] = {}
                for rule_id in applied_rule_ids:
                    checker = self._rule_checkers.get(rule_id)
                    if checker:
                        post_findings_by_rule[rule_id] = checker.check(ir_after, self.profile)

                # Check that every applied finding has been genuinely resolved
                for f_applied in applied_findings:
                    rule_post = post_findings_by_rule.get(f_applied.rule_id, [])
                    # Check if the specific targeted issue still persists
                    still_present = False
                    for p in rule_post:
                        if p.location.id == f_applied.location.id:
                            if f_applied.changes_text:
                                # For word rewrite proposals (B002), compare snippet / target word
                                if (
                                    p.evidence.snippet.strip().lower()
                                    == f_applied.evidence.snippet.strip().lower()
                                ):
                                    still_present = True
                                    break
                            else:
                                # For structural / format rules (W001, W006, W008, W010)
                                still_present = True
                                break
                    if still_present:
                        failed_targeted_findings.append(f_applied)

                if failed_targeted_findings:
                    if out.exists():
                        out.unlink()
                    reasons = [
                        f"{f.rule_id} ({f.rule_name}) pada {f.location.label}"
                        for f in failed_targeted_findings
                    ]
                    raise RollbackError(
                        f"Violasi Invarian 4: Analisis ulang mendeteksi temuan belum tuntas setelah perbaikan: "
                        f"{', '.join(reasons)}. Berkas hasil dibatalkan (rollback)."
                    )
            except RollbackError:
                raise
            except Exception as e:
                # If re-analysis or docx parsing crashes, rollback immediately
                if out.exists():
                    out.unlink()
                raise RollbackError(f"Gagal memverifikasi berkas hasil perbaikan ({e}). Rollback dilakukan.")

        return {
            "src_path": str(src),
            "out_path": str(out),
            "total_requested": len(findings),
            "fixes_applied": len([d for d in applied_details if d.get("status") == "applied"]),
            "applied_rule_ids": list(applied_rule_ids),
            "details": applied_details,
            "reanalysis_clean": True,
        }
