"""Sextuple — the full coordinate record data structure.

(entity, facet, value, t, observer, viewpoint)

Position facets: observer/viewpoint omittable → 4 fields sufficient.
Distance facets: observer/viewpoint MANDATORY → all 6 fields required.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FacetDefinition:
    """Definition of a coordinate axis (facet) in the domain."""

    name: str
    description: str
    facet_type: str  # "enum", "enum[]", "numeric", "string", etc.
    values: list[str] | None = None  # for enum types
    ordered: bool = False
    nature: str = "unclassified"  # "position" | "distance" | "unclassified"
    temporal_type: str = "none"  # "static" | "state" | "gradient" | "none"
    parent_facet: str | None = None  # for fractal decomposition
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_position(self) -> bool:
        return self.nature == "position"

    def is_distance(self) -> bool:
        return self.nature == "distance"


@dataclass
class Sextuple:
    """Full coordinate record: (entity, facet, value, t, observer, viewpoint).

    Position facets need only entity, facet, value (+ optional t).
    Distance facets require all 6 fields (C4 provenance).
    """

    entity: str
    facet: str
    value: Any
    t: str | None = None  # ISO 8601 timestamp
    observer: str | None = None
    viewpoint: str | None = None
    source_type: str = "estimated"  # "computed" | "observed" | "estimated"
    estimation_quality: str | None = None  # "converged" | None

    def is_complete_position(self) -> bool:
        """Check if this record is complete for a position facet."""
        return self.entity is not None and self.facet is not None and self.value is not None

    def is_complete_distance(self) -> bool:
        """Check if this record is complete for a distance facet (C4)."""
        return (
            self.is_complete_position()
            and self.observer is not None
            and self.viewpoint is not None
        )

    def validate(self, facet_def: FacetDefinition | None = None) -> list[str]:
        """Validate this record. Returns list of issues (empty = valid)."""
        issues = []

        if not self.entity:
            issues.append("missing entity")
        if not self.facet:
            issues.append("missing facet")
        if self.value is None:
            issues.append("missing value")
        if self.source_type not in ("computed", "observed", "estimated"):
            issues.append(f"invalid source_type: {self.source_type}")

        if self.source_type == "observed":
            if not self.observer:
                issues.append("observed value missing observer (C4)")
            if not self.viewpoint:
                issues.append("observed value missing viewpoint (C4)")

        if facet_def:
            if facet_def.is_distance():
                if not self.observer:
                    issues.append("distance facet missing observer (C4)")
                if not self.viewpoint:
                    issues.append("distance facet missing viewpoint (C4)")
            if facet_def.values and self.value not in facet_def.values:
                issues.append(f"value '{self.value}' not in enum: {facet_def.values}")

        if self.estimation_quality == "converged" and self.source_type != "estimated":
            issues.append("estimation_quality='converged' only valid for estimated values")

        return issues
