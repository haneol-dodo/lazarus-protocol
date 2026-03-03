"""Auditor 2 — Calculator Boundary Enforcement (계산기 감시).

Detects: compression (C1), prose-only (C3), provenance gaps (C4),
interpolation (C5), source_type violations (C6), LLM-as-ground-truth (C7),
metric optimization (C8), plan violations (C9).

Extracted from Parallax engine/audit.py, generalized for any Lazarus domain.
"""

import json
import subprocess
from pathlib import Path

from .core import AuditReport, BaseAuditor, Violation
from .checks import (
    check_source_type,
    check_no_compression,
    check_coordinate_output,
    check_observation_provenance,
    check_triangulation_integrity,
    check_cross_validation_terminology,
    detect_plan_violations_staged,
    detect_pipeline_manipulation_staged,
)


class CalculatorBoundaryAuditor(BaseAuditor):
    """Auditor 2: enforces calculator boundary constraints on data files."""

    def __init__(
        self,
        project_root: Path,
        data_dir: Path,
        pipeline_dir: str = "engine/autocoord/",
        coordinate_subdir: str | None = None,
        valid_pipeline_prefix: str = "engine.",
        min_convergence_runs: int = 18,
        min_convergence_families: int = 2,
        min_convergence_agreement: float = 70,
    ):
        super().__init__(project_root)
        self.data_dir = data_dir
        self.pipeline_dir = pipeline_dir
        self.coordinate_subdir = coordinate_subdir
        self.valid_pipeline_prefix = valid_pipeline_prefix
        self.min_convergence_runs = min_convergence_runs
        self.min_convergence_families = min_convergence_families
        self.min_convergence_agreement = min_convergence_agreement

    def _run_checks(self, data: dict, file_path: str, report: AuditReport):
        """Run all check functions on a data dict."""
        check_source_type(
            data, file_path, report,
            min_convergence_runs=self.min_convergence_runs,
            min_convergence_families=self.min_convergence_families,
            min_convergence_agreement=self.min_convergence_agreement,
            valid_pipeline_prefix=self.valid_pipeline_prefix,
        )
        check_no_compression(data, file_path, report)
        check_coordinate_output(data, file_path, report)
        check_observation_provenance(data, file_path, report)
        check_triangulation_integrity(data, file_path, report)
        check_cross_validation_terminology(data, file_path, report)

    def audit_file(self, file_path: Path, report: AuditReport):
        report.checked_files.append(str(file_path))
        try:
            with open(file_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C6",
                tag="[UNTAGGED_DATA]",
                file_path=str(file_path),
                detail=f"Cannot parse file: {e}",
            ))
            return

        self._run_checks(data, str(file_path), report)

    def audit_staged(self, report: AuditReport):
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=self.project_root,
            )
            staged = [f for f in result.stdout.strip().split("\n") if f]
        except (subprocess.SubprocessError, FileNotFoundError):
            return

        data_rel = str(self.data_dir.relative_to(self.project_root))
        for rel_path in staged:
            if rel_path.startswith(f"{data_rel}/") and rel_path.endswith(".json"):
                abs_path = self.project_root / rel_path
                if abs_path.exists():
                    self.audit_file(abs_path, report)

        detect_pipeline_manipulation_staged(
            report, self.project_root, self.pipeline_dir,
        )
        detect_plan_violations_staged(report, self.project_root)

    def audit_full(self, report: AuditReport):
        # Check coordinate subdirectory if configured
        if self.coordinate_subdir:
            coord_dir = self.data_dir / self.coordinate_subdir
            if coord_dir.exists():
                for json_file in sorted(coord_dir.glob("*.json")):
                    self.audit_file(json_file, report)

        # Check top-level data files that look like coordinate data
        for json_file in sorted(self.data_dir.glob("*.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if "words" in data and any(
                    "coordinates" in w for w in data.get("words", [])[:1]
                ):
                    self.audit_file(json_file, report)
            except (json.JSONDecodeError, OSError):
                pass
