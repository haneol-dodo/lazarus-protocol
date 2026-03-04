"""Experiment discovery and validation.

Scans a project's experiments/ directory to find and validate experiment documents.
"""

import re
from pathlib import Path

from .core import Experiment, ExperimentState


# Required sections in an experiment document
REQUIRED_SECTIONS = ["objective", "protocol", "status"]

# Optional but recommended sections
RECOMMENDED_SECTIONS = ["results", "conclusion", "files"]


def find_experiments(project_root: str | Path) -> list[Experiment]:
    """Scan experiments/ directory for experiment documents.

    Looks for files matching NNN_*.md pattern and extracts metadata.
    """
    exp_dir = Path(project_root) / "experiments"
    if not exp_dir.exists():
        return []

    experiments = []
    for md_file in sorted(exp_dir.glob("[0-9][0-9][0-9]_*.md")):
        exp_id = md_file.name[:3]
        title = md_file.stem[4:].replace("_", " ")

        # Try to extract state from file content
        state = _extract_state(md_file)

        experiments.append(Experiment(
            id=exp_id,
            title=title,
            branch=f"exp-{exp_id}",
            state=state,
            files=[str(md_file.relative_to(project_root))],
        ))

    return experiments


def _extract_state(md_path: Path) -> ExperimentState:
    """Extract experiment state from document content."""
    try:
        text = md_path.read_text(encoding="utf-8").lower()
    except (OSError, UnicodeDecodeError):
        return ExperimentState.design

    # Look for status indicators
    if "status: merged" in text or "status:** merged" in text:
        return ExperimentState.merged
    if "status: abandoned" in text or "status:** abandoned" in text:
        return ExperimentState.abandoned
    if "status: analysis" in text or "status:** analysis" in text:
        return ExperimentState.analysis
    if "status: full" in text or "full run" in text:
        return ExperimentState.full_run
    if "status: pilot" in text or "pilot" in text:
        return ExperimentState.pilot

    return ExperimentState.design


def detect_experiment_branch(branch_name: str) -> str | None:
    """Extract experiment ID from a branch name.

    Patterns:
        exp-010-convergence → "010"
        worktree-exp-010-convergence → "010"
        exp-005-200survey → "005"
        feature/something → None
    """
    m = re.search(r"exp-(\d{3})", branch_name)
    return m.group(1) if m else None


def validate_experiment_doc(
    exp_id: str,
    project_root: str | Path,
) -> list[str]:
    """Check that an experiment document has required sections.

    Returns a list of missing section names (empty = valid).
    """
    exp_dir = Path(project_root) / "experiments"
    if not exp_dir.exists():
        return [f"experiments/ directory not found"]

    # Find the experiment file
    matches = list(exp_dir.glob(f"{exp_id}_*.md"))
    if not matches:
        return [f"No experiment document found for EXP-{exp_id}"]

    doc_path = matches[0]
    try:
        text = doc_path.read_text(encoding="utf-8").lower()
    except (OSError, UnicodeDecodeError):
        return [f"Cannot read {doc_path}"]

    missing = []
    for section in REQUIRED_SECTIONS:
        # Check for section as heading or bold label
        if not (
            re.search(rf"#+\s*{section}", text)
            or re.search(rf"\*\*{section}", text)
            or re.search(rf"^{section}\s*:", text, re.MULTILINE)
        ):
            missing.append(section)

    return missing
