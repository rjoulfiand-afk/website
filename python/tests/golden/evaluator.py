"""Golden dataset evaluation framework.

Calculates precision, recall, and F1-score per rule by comparing
actual findings against expected findings in golden test cases.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rapikan.converter.docx_converter import convert_docx
from rapikan.ir.finding_schema import Finding
from rapikan.rules.campus_profile import CampusProfile, DEFAULT_PROFILE
from rapikan.rules.registry import RuleRegistry


@dataclass
class RuleMetric:
    rule_id: str
    tp: int = 0  # True positive: expected and found
    fp: int = 0  # False positive: found but not expected
    fn: int = 0  # False negative: expected but not found

    @property
    def precision(self) -> float:
        total = self.tp + self.fp
        return self.tp / total if total > 0 else 1.0

    @property
    def recall(self) -> float:
        total = self.tp + self.fn
        return self.tp / total if total > 0 else 1.0

    @property
    def f1(self) -> float:
        p = self.precision
        r = self.recall
        return (2 * p * r) / (p + r) if (p + r) > 0 else 1.0


@dataclass
class EvaluationReport:
    metrics_per_rule: dict[str, RuleMetric] = field(default_factory=dict)
    total_expected: int = 0
    total_actual: int = 0

    @property
    def overall_precision(self) -> float:
        tp = sum(m.tp for m in self.metrics_per_rule.values())
        fp = sum(m.fp for m in self.metrics_per_rule.values())
        return tp / (tp + fp) if (tp + fp) > 0 else 1.0

    @property
    def overall_recall(self) -> float:
        tp = sum(m.tp for m in self.metrics_per_rule.values())
        fn = sum(m.fn for m in self.metrics_per_rule.values())
        return tp / (tp + fn) if (tp + fn) > 0 else 1.0

    def summary(self) -> dict[str, Any]:
        return {
            "total_expected": self.total_expected,
            "total_actual": self.total_actual,
            "precision": round(self.overall_precision, 4),
            "recall": round(self.overall_recall, 4),
            "per_rule": {
                k: {
                    "tp": v.tp,
                    "fp": v.fp,
                    "fn": v.fn,
                    "precision": round(v.precision, 4),
                    "recall": round(v.recall, 4),
                    "f1": round(v.f1, 4),
                }
                for k, v in sorted(self.metrics_per_rule.items())
            },
        }


class GoldenEvaluator:
    """Evaluates Rapikan rules against golden test cases."""

    def __init__(
        self,
        registry: RuleRegistry | None = None,
        profile: CampusProfile | None = None,
    ):
        if registry is None:
            self.registry = RuleRegistry()
            self.registry.load_all()
        else:
            self.registry = registry
        self.profile = profile or DEFAULT_PROFILE

    def evaluate_case(
        self,
        docx_path: Path,
        expected_json_path: Path,
    ) -> list[tuple[str, str]]:  # list of (rule_id, match_status)
        """Run analysis on docx_path and compare against expected findings."""
        with open(expected_json_path, "r", encoding="utf-8") as fh:
            expected_data: list[dict] = json.load(fh)

        # Run pipeline
        ir = convert_docx(docx_path)
        rules = self.registry.get_rules(phase=1)

        actual_findings: list[Finding] = []
        for r in rules:
            actual_findings.extend(r.check(ir, self.profile))

        return self._compare_findings(actual_findings, expected_data)

    def _compare_findings(
        self,
        actual: list[Finding],
        expected: list[dict],
    ) -> list[tuple[str, str]]:
        # Match by (rule_id, location_id)
        expected_set = {
            (exp["rule_id"], exp.get("location_id"))
            for exp in expected
        }
        actual_set = {
            (f.rule_id, f.location.id)
            for f in actual
        }

        results = []
        # True Positives
        for item in actual_set & expected_set:
            results.append((item[0], "TP"))
        # False Positives
        for item in actual_set - expected_set:
            results.append((item[0], "FP"))
        # False Negatives
        for item in expected_set - actual_set:
            results.append((item[0], "FN"))

        return results

    def run_suite(self, golden_dir: Path) -> EvaluationReport:
        """Run all test cases in golden_dir."""
        report = EvaluationReport()

        case_dirs = [d for d in golden_dir.iterdir() if d.is_dir()]
        for case in case_dirs:
            docx_files = list(case.glob("*.docx"))
            expected_files = list(case.glob("expected_findings.json"))
            if not docx_files or not expected_files:
                continue

            docx_path = docx_files[0]
            expected_path = expected_files[0]

            with open(expected_path, "r", encoding="utf-8") as f:
                exp_list = json.load(f)
            report.total_expected += len(exp_list)

            results = self.evaluate_case(docx_path, expected_path)
            report.total_actual += sum(1 for _, s in results if s in ("TP", "FP"))

            for rule_id, status in results:
                if rule_id not in report.metrics_per_rule:
                    report.metrics_per_rule[rule_id] = RuleMetric(rule_id=rule_id)
                metric = report.metrics_per_rule[rule_id]
                if status == "TP":
                    metric.tp += 1
                elif status == "FP":
                    metric.fp += 1
                elif status == "FN":
                    metric.fn += 1

        return report
