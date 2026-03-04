"""Tests for lazarus.audit.logbook_auditor — Auditor 3 staged/full checks."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lazarus.audit.core import AuditReport
from lazarus.audit.logbook_auditor import LogbookExperimentAuditor


class TestLogbookExperimentAuditorFile(unittest.TestCase):
    """Test audit_file — logbook entry validation."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auditor = LogbookExperimentAuditor(
            project_root=Path(self.tmpdir),
        )

    def test_valid_logbook_entry(self):
        report = AuditReport()
        entry_path = Path(self.tmpdir) / "042_test.md"
        entry_path.write_text(
            "# 042 — Test\n\n"
            "> **Date:** 260304\n"
            "> **Build:** v1.0\n"
            "> **Trigger:** test\n\n"
            "Content here.\n"
        )
        self.auditor.audit_file(entry_path, report)
        self.assertTrue(report.auditor3_pass)
        self.assertEqual(len(report.violations), 0)

    def test_missing_date_field(self):
        report = AuditReport()
        entry_path = Path(self.tmpdir) / "043_bad.md"
        entry_path.write_text(
            "# 043 — Bad Entry\n\n"
            "> **Build:** v1.0\n"
            "> **Trigger:** test\n\n"
            "No date field.\n"
        )
        self.auditor.audit_file(entry_path, report)
        self.assertFalse(report.auditor3_pass)
        self.assertEqual(len(report.violations), 1)
        self.assertEqual(report.violations[0].tag, "[LOGBOOK_INCOMPLETE]")
        self.assertIn("Date:", report.violations[0].detail)

    def test_missing_all_fields(self):
        report = AuditReport()
        entry_path = Path(self.tmpdir) / "044_empty.md"
        entry_path.write_text("# 044 — Empty\n\nJust a title.\n")
        self.auditor.audit_file(entry_path, report)
        self.assertFalse(report.auditor3_pass)
        self.assertEqual(len(report.violations), 1)
        self.assertIn("Date:", report.violations[0].detail)
        self.assertIn("Build:", report.violations[0].detail)
        self.assertIn("Trigger:", report.violations[0].detail)

    def test_unreadable_file(self):
        report = AuditReport()
        entry_path = Path(self.tmpdir) / "nonexistent.md"
        self.auditor.audit_file(entry_path, report)
        self.assertFalse(report.auditor3_pass)
        self.assertEqual(report.violations[0].tag, "[LOGBOOK_UNREADABLE]")


class TestLogbookExperimentAuditorStaged(unittest.TestCase):
    """Test audit_staged — meaningful commit detection and experiment branch checks."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auditor = LogbookExperimentAuditor(
            project_root=Path(self.tmpdir),
        )

    def _mock_staged(self, diff_text="", staged_files=None, branch="main"):
        """Helper to mock git operations."""
        staged_files = staged_files or []
        return (
            patch.object(self.auditor, "_get_staged_diff", return_value=diff_text),
            patch.object(self.auditor, "_get_staged_files", return_value=staged_files),
            patch.object(self.auditor, "_get_current_branch", return_value=branch),
        )

    def test_meaningful_commit_without_logbook(self):
        diff = (
            "diff --git a/engine/new.py b/engine/new.py\n"
            "+++ b/engine/new.py\n"
            "@@ -0,0 +1 @@\n"
            "+def new(): pass\n"
        )
        patches = self._mock_staged(
            diff_text=diff,
            staged_files=["engine/new.py"],
        )
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        self.assertFalse(report.auditor3_pass)
        self.assertEqual(report.violations[0].tag, "[NO_LOGBOOK]")

    def test_meaningful_commit_with_logbook(self):
        diff = (
            "diff --git a/engine/new.py b/engine/new.py\n"
            "+++ b/engine/new.py\n"
            "@@ -0,0 +1 @@\n"
            "+def new(): pass\n"
        )
        patches = self._mock_staged(
            diff_text=diff,
            staged_files=["engine/new.py", "logbook/042_new.md"],
        )
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        # No [NO_LOGBOOK] violation
        logbook_violations = [v for v in report.violations if v.tag == "[NO_LOGBOOK]"]
        self.assertEqual(len(logbook_violations), 0)

    def test_trivial_commit_no_warning(self):
        patches = self._mock_staged(
            diff_text="",
            staged_files=["README.md"],
        )
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        self.assertTrue(report.auditor3_pass)
        self.assertEqual(len(report.violations), 0)

    def test_experiment_branch_without_doc(self):
        exp_dir = Path(self.tmpdir) / "experiments"
        exp_dir.mkdir()
        patches = self._mock_staged(
            staged_files=["engine/test.py"],
            branch="exp-010-convergence",
        )
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        exp_violations = [v for v in report.violations if v.tag == "[NO_EXPERIMENT_DOC]"]
        self.assertEqual(len(exp_violations), 1)
        self.assertIn("EXP-010", exp_violations[0].detail)

    def test_experiment_branch_with_doc(self):
        exp_dir = Path(self.tmpdir) / "experiments"
        exp_dir.mkdir()
        (exp_dir / "010_convergence.md").write_text("# EXP-010")
        patches = self._mock_staged(
            staged_files=["engine/test.py"],
            branch="exp-010-convergence",
        )
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        exp_violations = [v for v in report.violations if v.tag == "[NO_EXPERIMENT_DOC]"]
        self.assertEqual(len(exp_violations), 0)

    def test_enforce_disabled(self):
        auditor = LogbookExperimentAuditor(
            project_root=Path(self.tmpdir),
            enforce_logbook=False,
            enforce_experiment=False,
        )
        report = AuditReport()
        # Should return immediately without checking
        auditor.audit_staged(report)
        self.assertTrue(report.auditor3_pass)

    def test_no_staged_files(self):
        patches = self._mock_staged(staged_files=[])
        report = AuditReport()
        with patches[0], patches[1], patches[2]:
            self.auditor.audit_staged(report)
        self.assertTrue(report.auditor3_pass)


class TestLogbookExperimentAuditorFull(unittest.TestCase):
    """Test audit_full — experiment doc completeness."""

    def test_valid_experiment_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "010_test.md").write_text(
                "## Objective\nTest\n\n"
                "## Protocol\nSteps\n\n"
                "## Status\ndesign\n"
            )
            auditor = LogbookExperimentAuditor(project_root=Path(tmpdir))
            report = AuditReport()
            auditor.audit_full(report)
            self.assertTrue(report.auditor3_pass)

    def test_incomplete_experiment_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "010_test.md").write_text("# Just a title\n")
            auditor = LogbookExperimentAuditor(project_root=Path(tmpdir))
            report = AuditReport()
            auditor.audit_full(report)
            self.assertFalse(report.auditor3_pass)
            self.assertEqual(report.violations[0].tag, "[EXPERIMENT_DOC_INCOMPLETE]")

    def test_no_experiments_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            auditor = LogbookExperimentAuditor(project_root=Path(tmpdir))
            report = AuditReport()
            auditor.audit_full(report)
            self.assertTrue(report.auditor3_pass)  # no dir = nothing to check


class TestAuditReportAuditor3(unittest.TestCase):
    """Test that Auditor 3 violations route correctly in AuditReport."""

    def test_auditor3_violation_sets_flag(self):
        report = AuditReport()
        from lazarus.audit.core import Violation
        report.add(Violation(
            auditor="logbook_experiment",
            constraint="DOC",
            tag="[NO_LOGBOOK]",
            file_path="(staged)",
            detail="test",
            severity="minor",
        ))
        self.assertFalse(report.auditor3_pass)
        self.assertTrue(report.auditor1_pass)
        self.assertTrue(report.auditor2_pass)
        # passed still True (Auditor 3 is non-blocking)
        self.assertTrue(report.passed)
        # all_passed includes Auditor 3
        self.assertFalse(report.all_passed)

    def test_warnings_property(self):
        report = AuditReport()
        from lazarus.audit.core import Violation
        report.add(Violation(
            auditor="logbook_experiment",
            constraint="DOC",
            tag="[NO_LOGBOOK]",
            file_path="x",
            detail="minor issue",
            severity="minor",
        ))
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C6",
            tag="[MISSING_SOURCE_TYPE]",
            file_path="y",
            detail="critical issue",
            severity="critical",
        ))
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(report.warnings[0].tag, "[NO_LOGBOOK]")

    def test_summary_includes_auditor3(self):
        report = AuditReport()
        summary = report.summary()
        self.assertIn("Auditor 3 (Logbook/Experiment)", summary)
        self.assertIn("PASS", summary)


if __name__ == "__main__":
    unittest.main()
