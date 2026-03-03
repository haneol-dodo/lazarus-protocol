"""Tests for lazarus.audit.core — Violation, AuditReport, BaseAuditor."""

import unittest

from lazarus.audit.core import Violation, AuditReport, BaseAuditor


class TestViolation(unittest.TestCase):

    def test_creation(self):
        v = Violation(
            auditor="coordinate_integrity",
            constraint="C2",
            tag="[ENUM_INTEGRITY_VIOLATION]",
            file_path="enums/test.json",
            detail="Value added to enum",
        )
        self.assertEqual(v.auditor, "coordinate_integrity")
        self.assertEqual(v.constraint, "C2")
        self.assertEqual(v.severity, "critical")

    def test_custom_severity(self):
        v = Violation(
            auditor="calculator_boundary",
            constraint="C6",
            tag="[MISSING_SOURCE_TYPE]",
            file_path="data/test.json",
            detail="No source_type field",
            severity="major",
        )
        self.assertEqual(v.severity, "major")


class TestAuditReport(unittest.TestCase):

    def test_empty_report_passes(self):
        report = AuditReport()
        self.assertTrue(report.passed)
        self.assertTrue(report.auditor1_pass)
        self.assertTrue(report.auditor2_pass)
        self.assertEqual(len(report.violations), 0)

    def test_auditor1_violation_fails(self):
        report = AuditReport()
        v = Violation(
            auditor="coordinate_integrity",
            constraint="C2",
            tag="[ENUM_INTEGRITY_VIOLATION]",
            file_path="enums/test.json",
            detail="Enum value added",
        )
        report.add(v)
        self.assertFalse(report.auditor1_pass)
        self.assertTrue(report.auditor2_pass)
        self.assertFalse(report.passed)
        self.assertEqual(len(report.violations), 1)

    def test_auditor2_violation_fails(self):
        report = AuditReport()
        v = Violation(
            auditor="calculator_boundary",
            constraint="C6",
            tag="[MISSING_SOURCE_TYPE]",
            file_path="data/test.json",
            detail="No source_type",
        )
        report.add(v)
        self.assertTrue(report.auditor1_pass)
        self.assertFalse(report.auditor2_pass)
        self.assertFalse(report.passed)

    def test_both_auditors_fail(self):
        report = AuditReport()
        report.add(Violation(
            auditor="coordinate_integrity",
            constraint="C2", tag="[V1]",
            file_path="a.json", detail="issue 1",
        ))
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C6", tag="[V2]",
            file_path="b.json", detail="issue 2",
        ))
        self.assertFalse(report.auditor1_pass)
        self.assertFalse(report.auditor2_pass)
        self.assertFalse(report.passed)
        self.assertEqual(len(report.violations), 2)

    def test_checked_files(self):
        report = AuditReport()
        report.checked_files.append("file_a.json")
        report.checked_files.append("file_b.json")
        self.assertEqual(len(report.checked_files), 2)

    def test_summary_pass(self):
        report = AuditReport()
        report.checked_files = ["a.json", "b.json"]
        summary = report.summary(title="TEST REPORT")
        self.assertIn("TEST REPORT", summary)
        self.assertIn("PASS", summary)
        self.assertIn("Files checked: 2", summary)
        self.assertIn("Violations: 0", summary)

    def test_summary_fail_with_violations(self):
        report = AuditReport()
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C7",
            tag="[POC_FITTING]",
            file_path="data/bad.json",
            detail="Word-level overrides detected",
        ))
        summary = report.summary()
        self.assertIn("[STOP] AUDIT FAILED", summary)
        self.assertIn("[POC_FITTING]", summary)
        self.assertIn("C7", summary)
        self.assertIn("Word-level overrides", summary)

    def test_summary_default_title(self):
        report = AuditReport()
        summary = report.summary()
        self.assertIn("AUDIT REPORT", summary)

    def test_summary_custom_title(self):
        report = AuditReport()
        summary = report.summary(title="MY DOMAIN AUDIT")
        self.assertIn("MY DOMAIN AUDIT", summary)


class TestBaseAuditor(unittest.TestCase):

    def test_cannot_instantiate(self):
        """BaseAuditor is abstract — cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseAuditor(project_root="/tmp")


if __name__ == "__main__":
    unittest.main()
