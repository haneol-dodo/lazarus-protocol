"""Core audit data structures and base classes.

Extracted from Parallax engine/audit.py — generalized for any Lazarus domain.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Violation:
    """A single audit violation."""

    auditor: str  # e.g. "coordinate_integrity", "calculator_boundary"
    constraint: str  # e.g. "C2", "C6", "C7"
    tag: str  # e.g. "[ENUM_INTEGRITY_VIOLATION]", "[FALSE_COMPUTED]"
    file_path: str
    detail: str
    severity: str = "critical"  # "critical" | "major" | "minor"


@dataclass
class AuditReport:
    """Accumulates violations from one or more auditors."""

    violations: list[Violation] = field(default_factory=list)
    checked_files: list[str] = field(default_factory=list)
    auditor1_pass: bool = True
    auditor2_pass: bool = True

    @property
    def passed(self) -> bool:
        return self.auditor1_pass and self.auditor2_pass

    def add(self, v: Violation):
        self.violations.append(v)
        if v.auditor == "coordinate_integrity":
            self.auditor1_pass = False
        else:
            self.auditor2_pass = False

    def summary(self, title: str = "AUDIT REPORT") -> str:
        """Generate a human-readable summary of the audit results."""
        lines = []
        lines.append(title)
        lines.append("=" * 50)
        a1_tag = "PASS" if self.auditor1_pass else "FAIL"
        a2_tag = "PASS" if self.auditor2_pass else "FAIL"
        lines.append(f"Auditor 1 (Schema Integrity):     {a1_tag}")
        lines.append(f"Auditor 2 (Calculator Boundary):  {a2_tag}")
        lines.append(f"Files checked: {len(self.checked_files)}")
        lines.append(f"Violations: {len(self.violations)}")

        if self.violations:
            lines.append("")
            lines.append("VIOLATIONS")
            lines.append("-" * 50)
            for i, v in enumerate(self.violations, 1):
                lines.append(
                    f"[V-{i:03d}] {v.severity.upper()} — {v.constraint} {v.tag}"
                )
                lines.append(f"  File:   {v.file_path}")
                lines.append(f"  Detail: {v.detail}")
                lines.append("")

        lines.append("=" * 50)
        result = "PASS" if self.passed else "[STOP] AUDIT FAILED"
        lines.append(result)
        return "\n".join(lines)


class BaseAuditor(ABC):
    """Abstract base class for domain auditors."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @abstractmethod
    def audit_file(self, file_path: Path, report: AuditReport):
        """Audit a single file."""

    @abstractmethod
    def audit_staged(self, report: AuditReport):
        """Audit staged git changes."""

    @abstractmethod
    def audit_full(self, report: AuditReport):
        """Full system audit."""
