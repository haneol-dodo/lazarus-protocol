"""Pure audit check functions — constraint enforcement logic.

Each function takes data + file_path + report, and appends Violations
if constraints are broken. All thresholds are parameterized.

Extracted from Parallax engine/audit.py, generalized for any Lazarus domain.
"""

import re
import subprocess
from pathlib import Path

from .core import AuditReport, Violation


# ---------------------------------------------------------------------------
# C6: Source type classification
# ---------------------------------------------------------------------------

def check_source_type(
    data: dict,
    file_path: str,
    report: AuditReport,
    *,
    min_convergence_runs: int = 18,
    min_convergence_families: int = 2,
    min_convergence_agreement: float = 70,
    valid_pipeline_prefix: str = "engine.",
) -> None:
    """C6: Every coordinate data file must have source_type at batch or word level."""
    has_batch_source_type = "source_type" in data

    words = data.get("words", [])
    if not words and not has_batch_source_type:
        return  # Not a coordinate data file

    if not has_batch_source_type:
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C6",
            tag="[MISSING_SOURCE_TYPE]",
            file_path=file_path,
            detail="Coordinate data file missing batch-level 'source_type' field",
        ))

    # Check for false computed tags
    source_type = data.get("source_type")
    source = data.get("source", "")
    if source_type == "computed" and not source.startswith(valid_pipeline_prefix):
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C6",
            tag="[FALSE_COMPUTED]",
            file_path=file_path,
            detail=f"source_type='computed' but source='{source}' — "
                   f"computed values must come from {valid_pipeline_prefix}* pipeline",
            severity="critical",
        ))

    # Check batch-level convergence claims
    est_quality = data.get("estimation_quality")
    if est_quality == "converged":
        conv_meta = data.get("convergence_metadata", {})
        if not conv_meta:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C6",
                tag="[FALSE_CONVERGENCE]",
                file_path=file_path,
                detail="estimation_quality='converged' but no convergence_metadata",
                severity="critical",
            ))

    # Check word-level entries
    for i, word_entry in enumerate(words):
        coords = word_entry.get("coordinates", {})
        if not coords:
            continue
        word_source_type = word_entry.get("source_type", source_type)
        if word_source_type is None:
            word_name = word_entry.get("word", f"index_{i}")
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C6",
                tag="[MISSING_SOURCE_TYPE]",
                file_path=file_path,
                detail=f"Word '{word_name}' has no source_type "
                       f"(neither word-level nor batch-level)",
                severity="major",
            ))

        # Check word-level convergence claims
        word_est_quality = word_entry.get("estimation_quality")
        if word_est_quality == "converged":
            word_name = word_entry.get("word", f"index_{i}")
            conv_meta = word_entry.get("convergence_metadata", {})
            violations = []

            total_runs = conv_meta.get("total_runs", 0)
            if total_runs < min_convergence_runs:
                violations.append(f"runs={total_runs} < {min_convergence_runs}")

            families = conv_meta.get("families", [])
            if len(families) < min_convergence_families:
                violations.append(f"families={len(families)} < {min_convergence_families}")

            agreement = conv_meta.get("agreement_pct", 0)
            if agreement < min_convergence_agreement:
                violations.append(f"agreement={agreement}% < {min_convergence_agreement}%")

            if violations:
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C6",
                    tag="[FALSE_CONVERGENCE]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' estimation_quality='converged' "
                           f"but criteria not met: {'; '.join(violations)}",
                    severity="critical",
                ))


# ---------------------------------------------------------------------------
# C1: No compression
# ---------------------------------------------------------------------------

COMPRESSION_KEYS = frozenset({
    "summary", "average", "averaged", "merged", "aggregated",
    "combined_observations", "consensus",
})


def check_no_compression(
    data: dict,
    file_path: str,
    report: AuditReport,
) -> None:
    """C1: No averaging, summarizing, or merging of observation values."""
    found = set(data.keys()) & COMPRESSION_KEYS
    if found:
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C1",
            tag="[COMPRESSION_DETECTED]",
            file_path=file_path,
            detail=f"Batch-level field(s) suggest compressed observations: {found}. "
                   f"C1 requires keeping all observations with individual provenance.",
            severity="critical",
        ))

    for word_entry in data.get("words", []):
        word_name = word_entry.get("word", "?")
        word_compression = set(word_entry.keys()) & COMPRESSION_KEYS
        if word_compression:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C1",
                tag="[COMPRESSION_DETECTED]",
                file_path=file_path,
                detail=f"Word '{word_name}' has compression field(s): {word_compression}",
                severity="critical",
            ))

        observations = word_entry.get("observations", [])
        coords = word_entry.get("coordinates", {})
        if len(observations) > 1 and coords:
            has_individual_coords = all(
                "coordinates" in obs for obs in observations
            )
            if not has_individual_coords:
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C1",
                    tag="[COMPRESSION_DETECTED]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' has {len(observations)} observations "
                           f"but coordinates are not per-observation. "
                           f"Each observation must retain its own coordinate values.",
                    severity="major",
                ))


# ---------------------------------------------------------------------------
# C4: Observation provenance
# ---------------------------------------------------------------------------

PROVENANCE_FIELDS = frozenset({"observer", "viewpoint", "timestamp", "source"})


def check_observation_provenance(
    data: dict,
    file_path: str,
    report: AuditReport,
) -> None:
    """C4: Every observation record must include observer, viewpoint, timestamp, source."""
    if data.get("source_type") == "observed":
        missing = PROVENANCE_FIELDS - set(data.keys())
        if missing:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C4",
                tag="[INCOMPLETE_OBSERVATION]",
                file_path=file_path,
                detail=f"Batch source_type='observed' but missing provenance: {missing}",
                severity="critical",
            ))

    for word_entry in data.get("words", []):
        word_name = word_entry.get("word", "?")

        if word_entry.get("source_type") == "observed":
            missing = PROVENANCE_FIELDS - set(word_entry.keys())
            if missing:
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C4",
                    tag="[INCOMPLETE_OBSERVATION]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' source_type='observed' "
                           f"but missing provenance: {missing}",
                    severity="critical",
                ))

        for i, obs in enumerate(word_entry.get("observations", [])):
            missing = PROVENANCE_FIELDS - set(obs.keys())
            if missing:
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C4",
                    tag="[INCOMPLETE_OBSERVATION]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' observation[{i}] missing "
                           f"provenance fields: {missing}",
                    severity="critical",
                ))


# ---------------------------------------------------------------------------
# C5: Triangulation integrity
# ---------------------------------------------------------------------------

INTERPOLATION_KEYS = frozenset({
    "interpolated", "inferred", "imputed", "filled",
    "gap_filled", "extrapolated",
})


def check_triangulation_integrity(
    data: dict,
    file_path: str,
    report: AuditReport,
) -> None:
    """C5: No interpolation of missing values."""
    found = set(data.keys()) & INTERPOLATION_KEYS
    if found:
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C5",
            tag="[INTERPOLATION_DETECTED]",
            file_path=file_path,
            detail=f"Batch-level interpolation marker(s): {found}. "
                   f"C5 prohibits filling missing values.",
            severity="critical",
        ))

    if "effective_difficulty" in data or "triangulation" in data:
        if "completeness" not in data:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C5",
                tag="[INCOMPLETE_VECTOR]",
                file_path=file_path,
                detail="Triangulation output missing 'completeness' field. "
                       "Partial results must be explicitly marked.",
                severity="major",
            ))

    for word_entry in data.get("words", []):
        word_name = word_entry.get("word", "?")
        word_found = set(word_entry.keys()) & INTERPOLATION_KEYS
        if word_found:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C5",
                tag="[INTERPOLATION_DETECTED]",
                file_path=file_path,
                detail=f"Word '{word_name}' has interpolation marker(s): {word_found}",
                severity="critical",
            ))

        coords = word_entry.get("coordinates", {})
        if not isinstance(coords, dict):
            continue
        for gap_name, gap_data in coords.items():
            if isinstance(gap_data, dict):
                gap_found = set(gap_data.keys()) & INTERPOLATION_KEYS
                if gap_found:
                    report.add(Violation(
                        auditor="calculator_boundary",
                        constraint="C5",
                        tag="[INTERPOLATION_DETECTED]",
                        file_path=file_path,
                        detail=f"Word '{word_name}' {gap_name}: "
                               f"interpolation marker(s) {gap_found}",
                        severity="critical",
                    ))


# ---------------------------------------------------------------------------
# C3: Coordinate output
# ---------------------------------------------------------------------------

PROSE_KEYS = frozenset({
    "description", "text", "explanation", "note", "prose",
    "narrative", "paragraph",
})


def check_coordinate_output(
    data: dict,
    file_path: str,
    report: AuditReport,
) -> None:
    """C3: Output vectors, not prose."""
    words = data.get("words", [])
    if not words:
        return

    for word_entry in words:
        word_name = word_entry.get("word", "?")
        has_coords = "coordinates" in word_entry
        has_prose_only = bool(set(word_entry.keys()) & PROSE_KEYS) and not has_coords

        if has_prose_only:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C3",
                tag="[PROSE_WITHOUT_COORDINATES]",
                file_path=file_path,
                detail=f"Word '{word_name}' has prose field(s) but no 'coordinates'. "
                       f"C3 requires structured coordinate output, not prose.",
                severity="major",
            ))

        if has_coords:
            coords = word_entry["coordinates"]
            if isinstance(coords, str):
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C3",
                    tag="[PROSE_WITHOUT_COORDINATES]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' coordinates is a string, not a dict.",
                    severity="critical",
                ))
            elif isinstance(coords, dict) and not coords:
                report.add(Violation(
                    auditor="calculator_boundary",
                    constraint="C3",
                    tag="[PROSE_WITHOUT_COORDINATES]",
                    file_path=file_path,
                    detail=f"Word '{word_name}' has empty coordinates dict.",
                    severity="major",
                ))


# ---------------------------------------------------------------------------
# C8: Cross-validation terminology
# ---------------------------------------------------------------------------

def check_cross_validation_terminology(
    data: dict,
    file_path: str,
    report: AuditReport,
) -> None:
    """C8: cross-validation output should use disagreement terminology."""
    problematic_keys = {"match_rate", "error_rate", "accuracy"}
    found = set(data.keys()) & problematic_keys
    if found:
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C8",
            tag="[METRIC_OPTIMIZATION]",
            file_path=file_path,
            detail=f"Cross-validation uses optimization terminology: {found}. "
                   f"Use 'agreement_rate'/'disagreements' instead (measurement, not target)",
            severity="major",
        ))


# ---------------------------------------------------------------------------
# C9: Plan violations in staged diffs
# ---------------------------------------------------------------------------

def detect_plan_violations_staged(
    report: AuditReport,
    project_root: Path,
) -> None:
    """C9: Detect optimization language in staged diffs."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True, text=True, cwd=project_root,
        )
        diff_text = result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return

    if not diff_text:
        return

    plan_violation_patterns = [
        (re.compile(
            r'^\+.*(?:match|align|fit|calibrate)\s+(?:to|with|against)\s+'
            r'(?:poc|llm|gpt|claude|estimated)',
            re.IGNORECASE | re.MULTILINE,
        ), "C7", "Success criteria references matching LLM/POC output"),
        (re.compile(
            r'^\+.*(?:target|goal|objective|success)\s*[:=]?\s*'
            r'(?:match_rate|accuracy|mismatch.*(?:below|under|reduce))',
            re.IGNORECASE | re.MULTILINE,
        ), "C8", "Optimization target defined in plan"),
        (re.compile(
            r'^\+.*(?:reduce|decrease|lower|minimize)\s+'
            r'(?:mismatch|disagreement|error)',
            re.IGNORECASE | re.MULTILINE,
        ), "C8", "Mismatch reduction used as goal"),
        (re.compile(
            r'^\+.*pipeline\s+should\s+(?:output|produce|return|match)',
            re.IGNORECASE | re.MULTILINE,
        ), "C7", "Pipeline output prescribed to match external source"),
    ]

    for pattern, constraint, description in plan_violation_patterns:
        matches = pattern.findall(diff_text)
        if matches:
            examples = [m.strip()[:100] for m in matches[:3]]
            report.add(Violation(
                auditor="calculator_boundary",
                constraint=f"C9+{constraint}",
                tag="[PLAN_VIOLATION]",
                file_path="(staged diff)",
                detail=f"{description}. Found {len(matches)} instance(s): "
                       f"{examples}",
                severity="critical",
            ))


# ---------------------------------------------------------------------------
# C7: Pipeline manipulation in staged diffs
# ---------------------------------------------------------------------------

def detect_pipeline_manipulation_staged(
    report: AuditReport,
    project_root: Path,
    pipeline_dir: str = "engine/autocoord/",
) -> None:
    """C7: detect word-level override sets and threshold changes in staged pipeline code."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", pipeline_dir],
            capture_output=True, text=True, cwd=project_root,
        )
        diff_text = result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return

    if not diff_text:
        return

    # C7 Check 1: Word-level override sets
    set_pattern = re.compile(
        r'^\+.*(?:set\(|{)\s*"[a-z]+"(?:\s*,\s*"[a-z]+")+\s*[})]',
        re.MULTILINE,
    )
    matches = set_pattern.findall(diff_text)
    for match in matches:
        word_count = match.count('"') // 2
        if word_count >= 5:
            report.add(Violation(
                auditor="calculator_boundary",
                constraint="C7",
                tag="[POC_FITTING]",
                file_path=f"{pipeline_dir} (staged diff)",
                detail=f"Possible word-level override set ({word_count} words): "
                       f"{match[:120]}...",
                severity="critical",
            ))

    # C7 Check 2: Numeric threshold changes (skip new files)
    current_file = None
    is_new_file = False
    threshold_changes = []

    # Use a generic gap module pattern (configurable via subclass)
    gap_pattern = re.compile(r'gap\w+_')

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" b/")
            current_file = parts[-1] if len(parts) > 1 else None
            is_new_file = False
        elif line.startswith("new file mode"):
            is_new_file = True
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file and not is_new_file and gap_pattern.search(current_file or ""):
                num_pattern = re.compile(
                    r'(?:>|<|>=|<=|==)\s*(\d+\.?\d*)'
                    r'|'
                    r'(?:threshold|cutoff|boundary|band|bin|range)'
                    r'\s*[=:]\s*.*?(\d+\.?\d*)',
                    re.IGNORECASE,
                )
                if num_pattern.search(line):
                    threshold_changes.append((current_file, line.strip()))

    # C7 Check 3: Mapping dict value changes
    mapping_changes = []
    prev_removed = None
    current_file = None
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" b/")
            current_file = parts[-1] if len(parts) > 1 else None
        elif line.startswith("-") and not line.startswith("---"):
            if current_file and gap_pattern.search(current_file or ""):
                mapping_match = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
                if mapping_match:
                    prev_removed = (current_file, mapping_match.group(1),
                                    mapping_match.group(2), line.strip())
                else:
                    prev_removed = None
        elif line.startswith("+") and not line.startswith("+++"):
            if prev_removed and current_file == prev_removed[0]:
                mapping_match = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
                if mapping_match and mapping_match.group(1) == prev_removed[1]:
                    old_val = prev_removed[2]
                    new_val = mapping_match.group(2)
                    if old_val != new_val:
                        mapping_changes.append((
                            current_file, prev_removed[1], old_val, new_val,
                        ))
            prev_removed = None
        else:
            prev_removed = None

    if threshold_changes:
        files_affected = set(f for f, _ in threshold_changes)
        examples = [line for _, line in threshold_changes[:5]]
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C7",
            tag="[THRESHOLD_CHANGE]",
            file_path=", ".join(files_affected),
            detail=f"Numeric threshold(s) modified in pipeline module(s) "
                   f"({len(threshold_changes)} change(s)). "
                   f"Examples: {examples}. "
                   f"Threshold changes alter pipeline output — "
                   f"requires human review with justification.",
            severity="critical",
        ))

    if mapping_changes:
        files_affected = set(f for f, _, _, _ in mapping_changes)
        details = [f"{key}: {old}→{new}" for _, key, old, new
                   in mapping_changes[:5]]
        report.add(Violation(
            auditor="calculator_boundary",
            constraint="C7",
            tag="[MAPPING_CHANGE]",
            file_path=", ".join(files_affected),
            detail=f"Enum mapping(s) remapped in pipeline module(s) "
                   f"({len(mapping_changes)} change(s)). "
                   f"Examples: {details}. "
                   f"Remapping changes pipeline classification — "
                   f"requires human review with justification.",
            severity="critical",
        ))
