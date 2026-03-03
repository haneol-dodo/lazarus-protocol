"""Data types for convergence analysis results."""

from dataclasses import dataclass, field


@dataclass
class WordConvergenceResult:
    """Convergence state for a single word on a categorical axis."""

    word: str
    total_runs: int = 0
    distribution: dict[str, int] = field(default_factory=dict)
    mode: str | None = None
    agreement_pct: float = 0.0
    family_modes: dict[str, str] = field(default_factory=dict)
    cross_family_agreement: bool = False
    round_modes: dict[str, str] = field(default_factory=dict)
    mode_stable_rounds: int = 0
    converged: bool = False
    convergence_tier: int = 4
    convergence_round: int | None = None


@dataclass
class NumericWordResult:
    """Convergence state for a single word on a numeric axis."""

    word: str
    round_means: dict[int, float] = field(default_factory=dict)
    round_deltas: dict[int, float] = field(default_factory=dict)
    cumulative_stats: dict[int, dict] = field(default_factory=dict)
    converged_at: int | None = None
    convergence_speed: int | None = None
    current_mean: float | None = None
    current_sd: float | None = None
    total_runs: int = 0
    level: str | None = None


@dataclass
class AxisAnalysis:
    """Full convergence analysis for a categorical axis."""

    axis_id: str
    total_words: int = 0
    total_runs_per_word: int = 0
    enum_values: list[str] = field(default_factory=list)
    converged_count: int = 0
    converged_pct: float = 0.0
    tier_distribution: dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})
    value_distribution: dict[str, int] = field(default_factory=dict)
    words: dict[str, WordConvergenceResult] = field(default_factory=dict)
    hitl_queue: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class PilotResult:
    """Viability check result from pilot data."""

    viable: bool = False
    mean_agreement: float = 0.0
    single_value_dominant: bool = False
    recommendation: str = ""
    tier_distribution: dict[int, int] = field(default_factory=dict)
