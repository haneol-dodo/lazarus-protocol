"""Auditor 3 — Logbook & Experiment Documentation (문서화 감시).

Detects meaningful commits without logbook entries and experiment branches
without proper documentation. Non-blocking by default (minor severity).

Extracted as a generalized auditor for any Lazarus domain project.
"""

import re
import subprocess
from pathlib import Path

from .core import AuditReport, BaseAuditor, Violation
from ..logbook.generator import is_meaningful_commit


class LogbookExperimentAuditor(BaseAuditor):
    """Auditor 3: logbook and experiment documentation enforcement."""

    def __init__(
        self,
        project_root: Path,
        logbook_dir: str = "logbook",
        experiment_dir: str = "experiments",
        logbook_index: str = "INDEX.md",
        enforce_logbook: bool = True,
        enforce_experiment: bool = True,
        meaningful_patterns: list[str] | None = None,
    ):
        super().__init__(project_root)
        self.logbook_dir = logbook_dir
        self.experiment_dir = experiment_dir
        self.logbook_index = logbook_index
        self.enforce_logbook = enforce_logbook
        self.enforce_experiment = enforce_experiment
        self.meaningful_patterns = meaningful_patterns

    def audit_staged(self, report: AuditReport):
        """Check staged changes for documentation compliance.

        1. If meaningful commit and no logbook file staged → [NO_LOGBOOK]
        2. If on experiment branch and no experiment doc → [NO_EXPERIMENT_DOC]
        3. If logbook entry staged, validate required sections
        """
        if not self.enforce_logbook and not self.enforce_experiment:
            return

        # Get staged diff
        diff_text = self._get_staged_diff()
        staged_files = self._get_staged_files()

        if not staged_files:
            return

        # Check 1: meaningful commit without logbook entry
        if self.enforce_logbook and diff_text and is_meaningful_commit(diff_text):
            has_logbook = any(
                f.startswith(self.logbook_dir + "/") for f in staged_files
            )
            if not has_logbook:
                report.add(Violation(
                    auditor="logbook_experiment",
                    constraint="DOC",
                    tag="[NO_LOGBOOK]",
                    file_path="(staged changes)",
                    detail=(
                        "Meaningful commit detected but no logbook entry is staged. "
                        "Consider adding a logbook entry for this change."
                    ),
                    severity="minor",
                ))

        # Check 2: experiment branch without experiment doc
        if self.enforce_experiment:
            branch = self._get_current_branch()
            exp_id = self._detect_experiment_branch(branch)
            if exp_id:
                exp_dir = self.project_root / self.experiment_dir
                exp_docs = list(exp_dir.glob(f"{exp_id}_*.md")) if exp_dir.exists() else []
                if not exp_docs:
                    report.add(Violation(
                        auditor="logbook_experiment",
                        constraint="DOC",
                        tag="[NO_EXPERIMENT_DOC]",
                        file_path=f"experiments/{exp_id}_*.md",
                        detail=(
                            f"On experiment branch ({branch}) but no experiment "
                            f"document found for EXP-{exp_id}. "
                            f"Create experiments/{exp_id}_<name>.md with required sections."
                        ),
                        severity="minor",
                    ))

        # Check 3: validate staged logbook entries
        for fpath in staged_files:
            if fpath.startswith(self.logbook_dir + "/") and fpath.endswith(".md"):
                if fpath.endswith("INDEX.md"):
                    continue
                full_path = self.project_root / fpath
                if full_path.exists():
                    self.audit_file(full_path, report)

    def audit_file(self, file_path: Path, report: AuditReport):
        """Validate a logbook entry file for required sections."""
        report.checked_files.append(str(file_path))

        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            report.add(Violation(
                auditor="logbook_experiment",
                constraint="DOC",
                tag="[LOGBOOK_UNREADABLE]",
                file_path=str(file_path),
                detail=f"Cannot read logbook file: {file_path.name}",
                severity="minor",
            ))
            return

        # Required metadata fields in logbook entries
        required_fields = ["Date:", "Build:", "Trigger:"]
        missing = [f for f in required_fields if f not in text]

        if missing:
            report.add(Violation(
                auditor="logbook_experiment",
                constraint="DOC",
                tag="[LOGBOOK_INCOMPLETE]",
                file_path=str(file_path),
                detail=f"Logbook entry missing required fields: {', '.join(missing)}",
                severity="minor",
            ))

    def audit_full(self, report: AuditReport):
        """Check all experiment docs have required sections."""
        exp_dir = self.project_root / self.experiment_dir
        if not exp_dir.exists():
            return

        required_sections = ["objective", "protocol", "status"]

        for md_file in sorted(exp_dir.glob("[0-9][0-9][0-9]_*.md")):
            report.checked_files.append(str(md_file))
            try:
                text = md_file.read_text(encoding="utf-8").lower()
            except (OSError, UnicodeDecodeError):
                continue

            missing = []
            for section in required_sections:
                if not (
                    re.search(rf"#+\s*{section}", text)
                    or re.search(rf"\*\*{section}", text)
                    or re.search(rf"^{section}\s*:", text, re.MULTILINE)
                ):
                    missing.append(section)

            if missing:
                report.add(Violation(
                    auditor="logbook_experiment",
                    constraint="DOC",
                    tag="[EXPERIMENT_DOC_INCOMPLETE]",
                    file_path=str(md_file),
                    detail=(
                        f"Experiment document missing required sections: "
                        f"{', '.join(missing)}"
                    ),
                    severity="minor",
                ))

    # --- Private helpers ---

    def _get_staged_diff(self) -> str:
        """Get the staged git diff."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _get_staged_files(self) -> list[str]:
        """Get list of staged file paths."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _get_current_branch(self) -> str:
        """Get the current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    @staticmethod
    def _detect_experiment_branch(branch_name: str) -> str | None:
        """Extract experiment ID from branch name."""
        m = re.search(r"exp-(\d{3})", branch_name)
        return m.group(1) if m else None
