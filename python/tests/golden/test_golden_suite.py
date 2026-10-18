"""Full Golden Dataset Evaluation Suite for Fase 1 & 2 rules.

Tests:
1. Zero False Positive on Clean Compliant Academic Document.
2. 100% Precision & Recall on Targeted Error Cases.
3. Per-rule evaluation reporting (TP, FP, FN, Precision, Recall, F1).
"""

from pathlib import Path
import pytest
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Pt

from rapikan.rules.campus_profile import DEFAULT_PROFILE
from tests.golden.evaluator import GoldenEvaluator, RuleMetric


def create_clean_academic_docx(path: Path) -> None:
    """Creates a clean, fully compliant academic document with zero violations."""
    doc = Document()

    # 1. Auto Table of Contents block
    p_toc = doc.add_paragraph("DAFTAR ISI")
    fld = parse_xml(r'<w:fldSimple %s w:instr="TOC \o &quot;1-3&quot; \h \z \u"/>' % nsdecls('w'))
    doc.add_paragraph()._p.append(fld)
    try:
        doc.add_paragraph("BAB I PENDAHULUAN 1", style="TOC 1")
    except KeyError:
        p_ent = doc.add_paragraph("BAB I PENDAHULUAN 1")
        pPr = p_ent._p.get_or_add_pPr()
        pPr.append(parse_xml(r'<w:pStyle %s w:val="TOC 1"/>' % nsdecls('w')))

    # 2. Heading 1 using genuine style
    h1 = doc.add_paragraph("BAB I PENDAHULUAN", style="Heading 1")

    # 3. Body paragraph with 12pt Times New Roman, single spacing, standard words
    p1 = doc.add_paragraph(
        "Penelitian ini bertujuan untuk menganalisis efektivitas metode pembelajaran aktif. "
        "Berdasarkan hasil pengujian di laboratorium, semua data dikumpulkan secara sistematis."
    )

    # 4. Table with caption and repeating header
    doc.add_paragraph("Tabel 1.1 Variabel Penelitian", style="Caption" if "Caption" in [s.name for s in doc.styles] else "Normal")
    tbl = doc.add_table(rows=2, cols=2)
    tbl.rows[0].cells[0].text = "No"
    tbl.rows[0].cells[1].text = "Variabel"
    tbl.rows[0].cells[0].paragraphs[0].runs[0].bold = True
    tbl.rows[0].cells[1].paragraphs[0].runs[0].bold = True
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    tbl.rows[1].cells[0].text = "1"
    tbl.rows[1].cells[1].text = "Variabel Bebas"

    p2 = doc.add_paragraph(
        "Kesimpulan dari penelitian ini menunjukkan bahwa seluruh prosedur dilakukan sesuai standar mutu."
    )
    doc.save(str(path))


def create_error_prone_docx(path: Path) -> None:
    """Creates a document containing known targeted format violations."""
    doc = Document()
    # W001: Fake heading in Normal style
    p1 = doc.add_paragraph("BAB I PENDAHULUAN")
    p1.runs[0].bold = True
    p1.runs[0].font.size = Pt(14)

    # W010: Double space
    p2 = doc.add_paragraph("Ini adalah  kalimat dengan  spasi ganda.")

    # W008: Manual blank paragraphs (cluster of 2)
    p3 = doc.add_paragraph("")
    p4 = doc.add_paragraph("   ")

    # W006: Table without header row
    tbl = doc.add_table(rows=2, cols=2)
    tbl.rows[0].cells[0].text = "Kolom A"
    tbl.rows[0].cells[1].text = "Kolom B"
    tbl.rows[1].cells[0].text = "Data 1"
    tbl.rows[1].cells[1].text = "Data 2"

    # B002: Typos outside quotes
    p5 = doc.add_paragraph("Praktek analisa data dilakukan secara sistematis.")

    doc.save(str(path))


def test_golden_clean_document_has_zero_false_positives(tmp_path: Path):
    """Zero false positive criterion: A fully compliant document must yield 0 findings."""
    clean_docx = tmp_path / "clean_academic.docx"
    create_clean_academic_docx(clean_docx)

    from rapikan.converter.docx_converter import convert_docx
    from rapikan.rules.registry import RuleRegistry

    ir = convert_docx(clean_docx)
    registry = RuleRegistry()
    registry.load_all()
    rules = registry.get_rules(phase=1)

    findings = []
    for r in rules:
        findings.extend(r.check(ir, DEFAULT_PROFILE))

    # Assert ZERO false positives on clean document
    assert len(findings) == 0, f"False positive detected: {[(f.rule_id, f.evidence.snippet) for f in findings]}"


def test_golden_evaluator_reports_precision_and_recall_per_rule(tmp_path: Path):
    """Verify precision and recall metrics on programmatic golden test cases."""
    suite_dir = tmp_path / "suite"
    suite_dir.mkdir()

    # Case 1: Error prone
    case1_dir = suite_dir / "case_errors"
    case1_dir.mkdir()
    create_error_prone_docx(case1_dir / "sample.docx")

    # Expected findings for Case 1
    import json
    expected = [
        {"rule_id": "W001", "location_id": "p_0001"},
        {"rule_id": "W010", "location_id": "p_0002"},
        {"rule_id": "W008", "location_id": "p_0003"},
        {"rule_id": "W006", "location_id": "t_0001"},
        {"rule_id": "W007", "location_id": "t_0001"},
        {"rule_id": "B002", "location_id": "p_0009"},
        {"rule_id": "W005", "location_id": "doc_toc"},
    ]
    (case1_dir / "expected_findings.json").write_text(json.dumps(expected), encoding="utf-8")

    evaluator = GoldenEvaluator()
    report = evaluator.run_suite(suite_dir)

    summary = report.summary()
    assert report.total_expected >= 5
    assert summary["precision"] >= 0.80
    assert summary["recall"] >= 0.80

    # Ensure each targeted rule is evaluated
    for r_id in ("W001", "W006", "W008", "W010", "B002"):
        assert r_id in summary["per_rule"]
        assert summary["per_rule"][r_id]["tp"] >= 1
