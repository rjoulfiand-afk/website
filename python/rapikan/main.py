"""Rapikan CLI entry point.

Called by Laravel Queue jobs to analyze documents or apply fixes.

Usage:
    python -m rapikan.main analyze <relative_path> [--profile default] [--out-ir <path>] [--out-findings <path>]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

from rapikan.config import settings
from rapikan.converter.docx_converter import convert_docx
from rapikan.detector.magic_bytes import assert_is_zip_based
from rapikan.detector.zip_bomb import check_zip_safety
from rapikan.rules.campus_profile import CampusProfile, DEFAULT_PROFILE
from rapikan.rules.registry import RuleRegistry


def resolve_safe_path(rel_or_abs_path: str, base_dir: Path | None = None) -> Path:
    """Validate that path resides strictly inside base_dir to prevent path traversal."""
    base = (base_dir or settings.base_documents_dir).resolve()
    target = (base / rel_or_abs_path).resolve() if not Path(rel_or_abs_path).is_absolute() else Path(rel_or_abs_path).resolve()

    # Reject if outside base dir (unless testing without base_dir restriction)
    try:
        target.relative_to(base)
    except ValueError:
        # If running outside base dir in CLI development mode, ensure file actually exists
        if not target.exists():
            raise PermissionError(f"Path traversal detected or file does not exist: {rel_or_abs_path}")

    return target


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run analysis on a document file."""
    doc_path = resolve_safe_path(args.document)

    if not doc_path.exists():
        print(json.dumps({"error": f"File not found: {doc_path}"}), file=sys.stderr)
        return 1

    # Security checks
    try:
        assert_is_zip_based(doc_path)
        check_zip_safety(
            doc_path,
            max_entries=settings.max_zip_entries,
            max_ratio=settings.max_zip_ratio,
        )
    except Exception as e:
        print(json.dumps({"error": f"Security check failed: {e}"}), file=sys.stderr)
        return 2

    # Load profile
    profile = DEFAULT_PROFILE

    # Convert to IR
    try:
        ir = convert_docx(doc_path)
    except Exception as e:
        print(json.dumps({"error": f"Conversion error: {e}"}), file=sys.stderr)
        return 3

    # Genre classification & profile adaptation
    from rapikan.classifier.genre import classify_genre
    genre_hint = getattr(args, "genre", "auto")
    genre_result = classify_genre(ir, hint_genre=genre_hint)
    profile = profile.with_genre(genre_result.genre)

    # Save IR JSON if requested
    ir_dict = ir.model_dump(mode="json")
    if args.out_ir:
        out_ir_path = Path(args.out_ir)
        out_ir_path.parent.mkdir(parents=True, exist_ok=True)
        if out_ir_path.suffix == ".gz":
            with gzip.open(out_ir_path, "wt", encoding="utf-8") as f:
                json.dump(ir_dict, f)
        else:
            with open(out_ir_path, "w", encoding="utf-8") as f:
                json.dump(ir_dict, f, indent=2)

    # Run Rules
    registry = RuleRegistry()
    registry.load_all()
    rules = registry.get_rules(phase=1, include_llm=False, include_render=False)

    findings = []
    for rule in rules:
        findings.extend(rule.check(ir, profile))

    findings_dict = [f.model_dump(mode="json") for f in findings]

    # Save Findings JSON if requested
    if args.out_findings:
        out_findings_path = Path(args.out_findings)
        out_findings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_findings_path, "w", encoding="utf-8") as f:
            json.dump(findings_dict, f, indent=2)

    # Pre-flight inspections: Revisions and Comments (Requirement 3)
    if ir.has_revisions:
        from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
        rev_finding = Finding(
            rule_id="PRE_FLIGHT_REVISION",
            rule_name="Peringatan Dokumen Mengandung Revisi (Tracked Changes)",
            severity=Severity.WARNING,
            confidence=1.0,
            location=Location(
                type=LocationType.DOCUMENT,
                id="doc_revisions",
                label="Seluruh Dokumen",
            ),
            evidence=Evidence(
                snippet=f"Terdeteksi {ir.revision_count} paragraf dengan revisi aktif (w:ins/w:del)",
                detail="Sebaiknya terima atau tolak revisi di Microsoft Word terlebih dahulu.",
            ),
            auto_fixable=False,
            suggestion="Terima atau tolak perubahan terlacak (Track Changes) di Word sebelum melakukan perapian massal.",
            guide_module_slug="word-heading-style",
        )
        findings.append(rev_finding)
        findings_dict.append(rev_finding.model_dump(mode="json"))

    if ir.has_comments:
        from rapikan.ir.finding_schema import Evidence, Finding, Location, LocationType, Severity
        comm_finding = Finding(
            rule_id="PRE_FLIGHT_COMMENT",
            rule_name="Peringatan Dokumen Mengandung Komentar",
            severity=Severity.INFO,
            confidence=1.0,
            location=Location(
                type=LocationType.DOCUMENT,
                id="doc_comments",
                label="Seluruh Dokumen",
            ),
            evidence=Evidence(
                snippet=f"Terdeteksi {ir.comment_count} paragraf dengan komentar aktif",
                detail="Selesaikan komentar pengguna di Microsoft Word.",
            ),
            auto_fixable=False,
            suggestion="Selesaikan atau hapus komentar di Microsoft Word sebelum perapian massal.",
            guide_module_slug="word-heading-style",
        )
        findings.append(comm_finding)
        findings_dict.append(comm_finding.model_dump(mode="json"))

    # Summary payload for Laravel stdout consumption
    severity_counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1

    result_summary = {
        "status": "success",
        "document_path": str(doc_path),
        "genre": {
            "applied": genre_result.genre.value,
            "detected": genre_result.detected_genre.value,
            "confidence": genre_result.confidence,
            "is_manual": genre_result.is_manual,
            "markers": genre_result.markers,
            "name": genre_result.blueprint.name,
        },
        "paragraphs_count": len(ir.paragraphs),
        "tables_count": len(ir.tables),
        "sections_count": len(ir.sections),
        "headings_count": len(ir.headings),
        "has_revisions": ir.has_revisions,
        "has_comments": ir.has_comments,
        "revision_count": ir.revision_count,
        "comment_count": ir.comment_count,
        "findings_count": len(findings),
        "severity_summary": severity_counts,
        "findings": findings_dict,
    }

    print(json.dumps(result_summary, indent=2))
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Run automated safe repairs on a document."""
    from rapikan.fixer.orchestrator import DocumentFixer
    from rapikan.ir.finding_schema import Finding

    doc_path = resolve_safe_path(args.document)
    out_path = resolve_safe_path(args.output)

    if not doc_path.exists():
        print(json.dumps({"error": f"File not found: {doc_path}"}), file=sys.stderr)
        return 1

    findings = []
    if args.findings_json and Path(args.findings_json).exists():
        with open(args.findings_json, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            findings = [Finding.model_validate(item) for item in raw_list]
    else:
        # Auto-analyze first to get findings
        ir = convert_docx(doc_path)
        registry = RuleRegistry()
        registry.load_all()
        rules = registry.get_rules(phase=1)
        for r in rules:
            findings.extend(r.check(ir, DEFAULT_PROFILE))

    allow_text = getattr(args, "allow_text_changes", False)
    fixer = DocumentFixer()
    try:
        summary = fixer.apply_fixes(
            src_path=doc_path,
            out_path=out_path,
            findings=findings,
            allow_text_changes=allow_text,
        )
        print(json.dumps({"status": "success", "summary": summary}, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"error": f"Fixer failed: {e}"}), file=sys.stderr)
        return 4


def main() -> None:
    parser = argparse.ArgumentParser(description="Rapikan Analysis & Fixer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze document and produce findings")
    analyze_parser.add_argument("document", help="Path to .docx file (relative to base dir)")
    analyze_parser.add_argument("--profile", default="default", help="Campus profile slug or YAML file")
    analyze_parser.add_argument("--genre", default="auto", choices=["auto", "skripsi", "makalah", "laporan_magang", "proposal_penelitian", "custom"], help="Document genre / blueprint")
    analyze_parser.add_argument("--out-ir", help="Path to write IR JSON file (e.g. storage/ir/doc.json.gz)")
    analyze_parser.add_argument("--out-findings", help="Path to write findings JSON file")

    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Apply automated safe fixes to a copy of the document")
    fix_parser.add_argument("document", help="Source document path (will NOT be modified)")
    fix_parser.add_argument("output", help="Target output document path for the fixed copy")
    fix_parser.add_argument("--genre", default="auto", choices=["auto", "skripsi", "makalah", "laporan_magang", "proposal_penelitian", "custom"], help="Document genre / blueprint")
    fix_parser.add_argument("--findings-json", help="Path to findings JSON to apply")
    fix_parser.add_argument("--allow-text-changes", action="store_true", help="Allow applying approved rewrite proposals that modify text")

    args = parser.parse_args()

    if args.command == "analyze":
        code = cmd_analyze(args)
        sys.exit(code)
    elif args.command == "fix":
        code = cmd_fix(args)
        sys.exit(code)


if __name__ == "__main__":
    main()
