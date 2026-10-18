"""Test for the Golden Dataset Evaluator."""

import json
from pathlib import Path
from docx import Document
from docx.shared import Pt
from tests.golden.evaluator import GoldenEvaluator, EvaluationReport


def test_evaluator_metrics_calculation():
    """Verify precision and recall metric formulas."""
    report = EvaluationReport()
    # Add a mock rule with 2 TP, 0 FP, 0 FN (precision=1.0, recall=1.0)
    from tests.golden.evaluator import RuleMetric
    m1 = RuleMetric(rule_id="W001", tp=4, fp=1, fn=0)  # P = 4/5 = 0.8, R = 4/4 = 1.0
    report.metrics_per_rule["W001"] = m1

    assert round(m1.precision, 2) == 0.8
    assert round(m1.recall, 2) == 1.0
    assert m1.f1 > 0.88

    summary = report.summary()
    assert "W001" in summary["per_rule"]
    assert summary["per_rule"]["W001"]["precision"] == 0.8


def test_golden_evaluator_runs_on_case(tmp_path: Path):
    """Test running evaluator on a programmatic golden case."""
    case_dir = tmp_path / "case_01"
    case_dir.mkdir(parents=True)

    docx_path = case_dir / "sample.docx"
    doc = Document()
    p1 = doc.add_paragraph("Normal text.")
    # Add fake heading: bold + large in Normal style
    p2 = doc.add_paragraph("BAB I PENDAHULUAN")
    p2.runs[0].bold = True
    p2.runs[0].font.size = Pt(14)
    doc.save(str(docx_path))

    expected_path = case_dir / "expected_findings.json"
    expected_data = [
        {"rule_id": "W001", "location_id": "p_0002"}
    ]
    expected_path.write_text(json.dumps(expected_data), encoding="utf-8")

    evaluator = GoldenEvaluator()
    report = evaluator.run_suite(tmp_path)
    assert report.total_expected == 1
    # Check that W001 was evaluated
    assert "W001" in report.metrics_per_rule
    assert report.metrics_per_rule["W001"].tp == 1
    assert report.metrics_per_rule["W001"].fp == 0
    assert report.metrics_per_rule["W001"].precision == 1.0
