"""Auditor 1 — Schema Integrity (좌표계 감시).

Detects enum file mutations: value add/remove/rename, schema violations.
Enforces C2 (Enum Immutability).

Extracted from Parallax engine/audit.py, generalized for any Lazarus domain.
"""

import json
import subprocess
from pathlib import Path

from .core import AuditReport, BaseAuditor, Violation


class SchemaIntegrityAuditor(BaseAuditor):
    """Auditor 1: validates enum files against meta-schema and detects mutations."""

    def __init__(
        self,
        project_root: Path,
        schema_dir: Path,
        meta_schema_path: Path,
        file_glob: str = "gap*.json",
        coordinate_dirs: list[str] | None = None,
        framework_suffix: str = "_FRAMEWORK.json",
    ):
        super().__init__(project_root)
        self.schema_dir = schema_dir
        self.meta_schema_path = meta_schema_path
        self.file_glob = file_glob
        self.coordinate_dirs = coordinate_dirs
        self.framework_suffix = framework_suffix

    def _load_meta_schema(self) -> dict | None:
        if self.meta_schema_path.exists():
            with open(self.meta_schema_path) as f:
                return json.load(f)
        return None

    def _get_coordinate_dirs(self) -> list[str]:
        """Read valid coordinate directory names from meta-schema."""
        if self.coordinate_dirs:
            return self.coordinate_dirs
        schema = self._load_meta_schema()
        if schema:
            return schema.get("properties", {}).get("coordinate", {}).get("enum", [])
        return []

    def _validate_schema(self, file_path: Path, report: AuditReport):
        """Check that an enum file conforms to the meta-schema structure."""
        try:
            with open(file_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            report.add(Violation(
                auditor="coordinate_integrity",
                constraint="C2",
                tag="[ENUM_INTEGRITY_VIOLATION]",
                file_path=str(file_path),
                detail=f"Cannot parse enum file: {e}",
            ))
            return

        schema = self._load_meta_schema()
        if schema is None:
            report.add(Violation(
                auditor="coordinate_integrity",
                constraint="C2",
                tag="[ENUM_INTEGRITY_VIOLATION]",
                file_path=str(self.meta_schema_path),
                detail="Meta-schema file not found — cannot validate enum structure",
                severity="major",
            ))
            return

        # Required fields check
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                report.add(Violation(
                    auditor="coordinate_integrity",
                    constraint="C2",
                    tag="[ENUM_INTEGRITY_VIOLATION]",
                    file_path=str(file_path),
                    detail=f"Missing required field: '{key}'",
                ))

        # Validate coordinate field
        coord = data.get("coordinate")
        valid_coords = schema.get("properties", {}).get("coordinate", {}).get("enum", [])
        if coord and valid_coords and coord not in valid_coords:
            report.add(Violation(
                auditor="coordinate_integrity",
                constraint="C2",
                tag="[ENUM_INTEGRITY_VIOLATION]",
                file_path=str(file_path),
                detail=f"Invalid coordinate value: '{coord}' (must be one of {valid_coords})",
            ))

        # Validate axes have required fields
        axes = data.get("axes", {})
        for axis_name, axis_def in axes.items():
            if not isinstance(axis_def, dict):
                continue
            if "type" not in axis_def:
                report.add(Violation(
                    auditor="coordinate_integrity",
                    constraint="C2",
                    tag="[ENUM_INTEGRITY_VIOLATION]",
                    file_path=str(file_path),
                    detail=f"Axis '{axis_name}' missing required field 'type'",
                ))
            if "description" not in axis_def:
                report.add(Violation(
                    auditor="coordinate_integrity",
                    constraint="C2",
                    tag="[ENUM_INTEGRITY_VIOLATION]",
                    file_path=str(file_path),
                    detail=f"Axis '{axis_name}' missing required field 'description'",
                ))
            axis_type = axis_def.get("type")
            if axis_type in ("enum", "enum[]") and "values" not in axis_def:
                report.add(Violation(
                    auditor="coordinate_integrity",
                    constraint="C2",
                    tag="[ENUM_INTEGRITY_VIOLATION]",
                    file_path=str(file_path),
                    detail=f"Axis '{axis_name}' (type={axis_type}) missing 'values' array",
                ))

    def _detect_mutations_staged(self, report: AuditReport):
        """Detect enum value mutations in staged git changes."""
        enums_rel = str(self.schema_dir.relative_to(self.project_root))
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--", f"{enums_rel}/"],
                capture_output=True, text=True, cwd=self.project_root,
            )
            changed_files = [f for f in result.stdout.strip().split("\n") if f]
        except (subprocess.SubprocessError, FileNotFoundError):
            return

        for rel_path in changed_files:
            if not rel_path.endswith(".json"):
                continue
            if "_schema/" in rel_path:
                continue
            if rel_path.endswith(self.framework_suffix):
                continue

            abs_path = self.project_root / rel_path
            report.checked_files.append(rel_path)

            try:
                old_result = subprocess.run(
                    ["git", "show", f"HEAD:{rel_path}"],
                    capture_output=True, text=True, cwd=self.project_root,
                )
                if old_result.returncode != 0:
                    self._validate_schema(abs_path, report)
                    continue

                old_data = json.loads(old_result.stdout)
                with open(abs_path) as f:
                    new_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if new_data.get("status") == "draft":
                self._validate_schema(abs_path, report)
                continue

            old_axes = old_data.get("axes", {})
            new_axes = new_data.get("axes", {})

            for axis_name in old_axes:
                if axis_name not in new_axes:
                    report.add(Violation(
                        auditor="coordinate_integrity",
                        constraint="C2",
                        tag="[ENUM_INTEGRITY_VIOLATION]",
                        file_path=rel_path,
                        detail=f"Axis '{axis_name}' removed",
                    ))

            for axis_name, new_def in new_axes.items():
                old_def = old_axes.get(axis_name)
                if old_def is None:
                    report.add(Violation(
                        auditor="coordinate_integrity",
                        constraint="C2",
                        tag="[ENUM_INTEGRITY_VIOLATION]",
                        file_path=rel_path,
                        detail=f"Axis '{axis_name}' added (enum immutability)",
                    ))
                    continue

                old_values = set(old_def.get("values", []))
                new_values = set(new_def.get("values", []))
                removed = old_values - new_values
                added = new_values - old_values
                if removed:
                    report.add(Violation(
                        auditor="coordinate_integrity",
                        constraint="C2",
                        tag="[ENUM_INTEGRITY_VIOLATION]",
                        file_path=rel_path,
                        detail=f"Axis '{axis_name}': values removed: {removed}",
                    ))
                if added:
                    report.add(Violation(
                        auditor="coordinate_integrity",
                        constraint="C2",
                        tag="[ENUM_INTEGRITY_VIOLATION]",
                        file_path=rel_path,
                        detail=f"Axis '{axis_name}': values added: {added}",
                    ))

            self._validate_schema(abs_path, report)

    def audit_file(self, file_path: Path, report: AuditReport):
        report.checked_files.append(str(file_path))
        self._validate_schema(file_path, report)

    def audit_staged(self, report: AuditReport):
        self._detect_mutations_staged(report)

    def audit_full(self, report: AuditReport):
        for coord_dir_name in self._get_coordinate_dirs():
            coord_dir = self.schema_dir / coord_dir_name
            if not coord_dir.exists():
                continue
            for enum_file in sorted(coord_dir.glob(self.file_glob)):
                report.checked_files.append(
                    str(enum_file.relative_to(self.project_root))
                )
                self._validate_schema(enum_file, report)
