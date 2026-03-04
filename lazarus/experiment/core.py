"""Core experiment data structures and state machine.

Experiments follow a lifecycle: design → pilot → full_run → analysis → merged/abandoned.
State transitions are validated to prevent skipping steps.
"""

from dataclasses import dataclass, field
from enum import Enum


class ExperimentState(Enum):
    """Experiment lifecycle states."""

    design = "design"
    pilot = "pilot"
    full_run = "full_run"
    analysis = "analysis"
    merged = "merged"
    abandoned = "abandoned"


# Valid state transitions
VALID_TRANSITIONS: dict[ExperimentState, list[ExperimentState]] = {
    ExperimentState.design: [ExperimentState.pilot, ExperimentState.abandoned],
    ExperimentState.pilot: [ExperimentState.full_run, ExperimentState.design, ExperimentState.abandoned],
    ExperimentState.full_run: [ExperimentState.analysis, ExperimentState.abandoned],
    ExperimentState.analysis: [ExperimentState.merged, ExperimentState.full_run, ExperimentState.abandoned],
    ExperimentState.merged: [],  # terminal
    ExperimentState.abandoned: [],  # terminal
}


@dataclass
class Experiment:
    """An experiment instance with lifecycle tracking."""

    id: str  # e.g. "010"
    title: str
    branch: str  # e.g. "exp-010-convergence"
    state: ExperimentState = ExperimentState.design
    predecessor: str | None = None  # previous experiment ID
    files: list[str] = field(default_factory=list)
    created: str = ""  # ISO 8601
    updated: str = ""  # ISO 8601


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


def transition(exp: Experiment, new_state: ExperimentState) -> Experiment:
    """Validate and apply a state transition.

    Returns a new Experiment with updated state.
    Raises InvalidTransitionError if the transition is not allowed.
    """
    allowed = VALID_TRANSITIONS.get(exp.state, [])
    if new_state not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {exp.state.value} to {new_state.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    return Experiment(
        id=exp.id,
        title=exp.title,
        branch=exp.branch,
        state=new_state,
        predecessor=exp.predecessor,
        files=exp.files,
        created=exp.created,
        updated=exp.updated,
    )
