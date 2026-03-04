"""Domain Registry — central configuration point for a Lazarus domain project.

A domain project creates one DomainRegistry instance and passes it to
auditors, convergence engines, and other components. This replaces
hardcoded paths and thresholds scattered across modules.
"""

from pathlib import Path

from ..audit.core import AuditReport
from ..audit.schema_auditor import SchemaIntegrityAuditor
from ..audit.boundary_auditor import CalculatorBoundaryAuditor
from ..audit.logbook_auditor import LogbookExperimentAuditor
from ..convergence.categorical import CategoricalConvergence
from ..convergence.numeric import NumericConvergence


class DomainRegistry:
    """Central configuration for a Lazarus domain instance."""

    def __init__(
        self,
        *,
        name: str,
        project_root: str | Path,
        schema_dir: str | Path,
        data_dir: str | Path,
        meta_schema_path: str | Path,
        pipeline_dir: str = "engine/autocoord/",
        coordinate_dirs: list[str] | None = None,
        coordinate_subdir: str | None = None,
        valid_pipeline_prefix: str = "engine.",
        constraints: list[str] | None = None,
        families: list[str] | None = None,
        models: list[str] | None = None,
        # Convergence defaults
        min_agreement: float = 0.70,
        min_stable_rounds: int = 2,
        tier_thresholds: dict[int, float] | None = None,
        pilot_viable_threshold: float = 0.40,
        runs_per_round: int = 6,
        max_rounds: int = 3,
        # Numeric convergence defaults
        numeric_threshold: float = 3.0,
        numeric_min_stable: int = 2,
        numeric_max_rounds: int = 7,
        # Audit convergence thresholds
        min_convergence_runs: int = 18,
        min_convergence_families: int = 2,
        min_convergence_agreement: float = 70,
        # Logbook/experiment config
        logbook_dir: str = "logbook",
        experiment_dir: str = "experiments",
        logbook_index: str = "INDEX.md",
        enforce_logbook: bool = True,
        enforce_experiment: bool = True,
    ):
        self.name = name
        self.project_root = Path(project_root)
        self.schema_dir = Path(schema_dir)
        self.data_dir = Path(data_dir)
        self.meta_schema_path = Path(meta_schema_path)
        self.pipeline_dir = pipeline_dir
        self.coordinate_dirs = coordinate_dirs
        self.coordinate_subdir = coordinate_subdir
        self.valid_pipeline_prefix = valid_pipeline_prefix
        self.constraints = constraints or [f"C{i}" for i in range(1, 11)]
        self.families = families or ["claude", "openai", "google"]
        self.models = models or ["haiku", "sonnet", "opus"]

        # Convergence config
        self.min_agreement = min_agreement
        self.min_stable_rounds = min_stable_rounds
        self.tier_thresholds = tier_thresholds or {1: 0.90, 2: 0.80, 3: 0.70}
        self.pilot_viable_threshold = pilot_viable_threshold
        self.runs_per_round = runs_per_round
        self.max_rounds = max_rounds
        self.numeric_threshold = numeric_threshold
        self.numeric_min_stable = numeric_min_stable
        self.numeric_max_rounds = numeric_max_rounds

        # Audit convergence thresholds
        self.min_convergence_runs = min_convergence_runs
        self.min_convergence_families = min_convergence_families
        self.min_convergence_agreement = min_convergence_agreement

        # Logbook/experiment config
        self.logbook_dir = logbook_dir
        self.experiment_dir = experiment_dir
        self.logbook_index = logbook_index
        self.enforce_logbook = enforce_logbook
        self.enforce_experiment = enforce_experiment

    def build_schema_auditor(self) -> SchemaIntegrityAuditor:
        """Build Auditor 1 configured for this domain."""
        return SchemaIntegrityAuditor(
            project_root=self.project_root,
            schema_dir=self.schema_dir,
            meta_schema_path=self.meta_schema_path,
            coordinate_dirs=self.coordinate_dirs,
        )

    def build_boundary_auditor(self) -> CalculatorBoundaryAuditor:
        """Build Auditor 2 configured for this domain."""
        return CalculatorBoundaryAuditor(
            project_root=self.project_root,
            data_dir=self.data_dir,
            pipeline_dir=self.pipeline_dir,
            coordinate_subdir=self.coordinate_subdir,
            valid_pipeline_prefix=self.valid_pipeline_prefix,
            min_convergence_runs=self.min_convergence_runs,
            min_convergence_families=self.min_convergence_families,
            min_convergence_agreement=self.min_convergence_agreement,
        )

    def build_logbook_auditor(self) -> LogbookExperimentAuditor:
        """Build Auditor 3 configured for this domain."""
        return LogbookExperimentAuditor(
            project_root=self.project_root,
            logbook_dir=self.logbook_dir,
            experiment_dir=self.experiment_dir,
            logbook_index=self.logbook_index,
            enforce_logbook=self.enforce_logbook,
            enforce_experiment=self.enforce_experiment,
        )

    def build_categorical_convergence(self) -> CategoricalConvergence:
        """Build a categorical convergence engine for this domain."""
        return CategoricalConvergence(
            min_agreement=self.min_agreement,
            min_stable_rounds=self.min_stable_rounds,
            tier_thresholds=self.tier_thresholds,
            pilot_viable_threshold=self.pilot_viable_threshold,
            families=self.families,
            runs_per_round=self.runs_per_round,
            max_rounds=self.max_rounds,
        )

    def build_numeric_convergence(self) -> NumericConvergence:
        """Build a numeric convergence engine for this domain."""
        return NumericConvergence(
            threshold=self.numeric_threshold,
            min_stable=self.numeric_min_stable,
            max_rounds=self.numeric_max_rounds,
            models=self.models,
        )

    def audit_staged(self) -> AuditReport:
        """Run all auditors on staged git changes."""
        report = AuditReport()
        self.build_schema_auditor().audit_staged(report)
        self.build_boundary_auditor().audit_staged(report)
        if self.enforce_logbook or self.enforce_experiment:
            self.build_logbook_auditor().audit_staged(report)
        return report

    def audit_full(self) -> AuditReport:
        """Run all auditors on the full system."""
        report = AuditReport()
        self.build_schema_auditor().audit_full(report)
        self.build_boundary_auditor().audit_full(report)
        if self.enforce_logbook or self.enforce_experiment:
            self.build_logbook_auditor().audit_full(report)
        return report
