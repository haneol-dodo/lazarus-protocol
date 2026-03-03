"""Categorical Convergence Engine.

Runs categorical enum axis filling via run-until-convergence.
Values are categorical enum strings (not numeric).
Convergence = mode stable for N rounds + agreement >= threshold.

Extracted from Parallax 010_categorical_convergence.py.
"""

from collections import Counter

from .types import WordConvergenceResult, AxisAnalysis, PilotResult


class CategoricalConvergence:
    """Engine for categorical convergence analysis.

    All thresholds configurable via constructor. No domain-specific
    references (no AXIS_REGISTRY, no Oxford 3000, no UBL prompts).
    """

    def __init__(
        self,
        *,
        min_agreement: float = 0.70,
        min_stable_rounds: int = 2,
        tier_thresholds: dict[int, float] | None = None,
        pilot_viable_threshold: float = 0.40,
        families: list[str] | None = None,
        runs_per_round: int = 6,
        max_rounds: int = 3,
    ):
        self.min_agreement = min_agreement
        self.min_stable_rounds = min_stable_rounds
        self.tier_thresholds = tier_thresholds or {1: 0.90, 2: 0.80, 3: 0.70}
        self.pilot_viable_threshold = pilot_viable_threshold
        self.families = families or ["claude", "openai", "google"]
        self.runs_per_round = runs_per_round
        self.max_rounds = max_rounds

    def compute_word_convergence(
        self,
        word: str,
        word_data: dict,
        enum_values: list[str],
    ) -> WordConvergenceResult:
        """Compute convergence state for a single word."""
        runs = word_data.get("runs", {})
        total_runs = len(runs)

        if total_runs == 0:
            return WordConvergenceResult(word=word)

        # Overall distribution
        values = [r["value"] for r in runs.values()]
        dist = Counter(values)
        mode = dist.most_common(1)[0][0]
        agreement = dist[mode] / total_runs

        # Per-family modes
        family_values: dict[str, list] = {}
        for run_id, run_info in runs.items():
            family = run_info.get("family", "unknown")
            if family not in family_values:
                family_values[family] = []
            family_values[family].append(run_info["value"])

        family_modes = {}
        for family, vals in family_values.items():
            fc = Counter(vals)
            family_modes[family] = fc.most_common(1)[0][0]

        cross_family = len(set(family_modes.values())) <= 1 if family_modes else False

        # Per-round modes (cumulative)
        round_runs: dict[int, list] = {}
        for run_id, run_info in runs.items():
            rnd = run_info.get("round", 1)
            if rnd not in round_runs:
                round_runs[rnd] = []
            round_runs[rnd].append(run_info["value"])

        cumulative_values: list[str] = []
        round_modes: dict[int, str] = {}
        for rnd in sorted(round_runs.keys()):
            cumulative_values.extend(round_runs[rnd])
            rc = Counter(cumulative_values)
            round_modes[rnd] = rc.most_common(1)[0][0]

        # Check mode stability
        mode_stable = 0
        prev_mode = None
        converged_at_round = None
        for rnd in sorted(round_modes.keys()):
            if round_modes[rnd] == prev_mode:
                mode_stable += 1
                if mode_stable >= self.min_stable_rounds and agreement >= self.min_agreement:
                    if converged_at_round is None:
                        converged_at_round = rnd
            else:
                mode_stable = 1
            prev_mode = round_modes[rnd]

        converged = converged_at_round is not None

        # Tier classification
        if not converged:
            tier = 4
        elif agreement >= self.tier_thresholds[1]:
            tier = 1
        elif agreement >= self.tier_thresholds[2]:
            tier = 2
        elif agreement >= self.tier_thresholds[3]:
            tier = 3
        else:
            tier = 4

        return WordConvergenceResult(
            word=word,
            total_runs=total_runs,
            distribution=dict(dist),
            mode=mode,
            agreement_pct=round(agreement * 100, 1),
            family_modes=family_modes,
            cross_family_agreement=cross_family,
            round_modes={str(k): v for k, v in round_modes.items()},
            mode_stable_rounds=mode_stable,
            converged=converged,
            convergence_tier=tier,
            convergence_round=converged_at_round,
        )

    def analyze_axis(self, data: dict) -> AxisAnalysis:
        """Full convergence analysis for an axis."""
        words_analysis: dict[str, WordConvergenceResult] = {}
        tier_dist = {1: 0, 2: 0, 3: 0, 4: 0}
        value_dist: Counter = Counter()
        max_runs = 0

        for word, word_data in data.get("words", {}).items():
            wc = self.compute_word_convergence(word, word_data, data["enum_values"])
            words_analysis[word] = wc
            tier_dist[wc.convergence_tier] += 1
            if wc.converged and wc.mode:
                value_dist[wc.mode] += 1
            max_runs = max(max_runs, wc.total_runs)

        total = len(words_analysis)
        converged = sum(1 for w in words_analysis.values() if w.converged)

        # HITL queue
        hitl: dict[str, list[str]] = {
            "skip": [],
            "sample_review": [],
            "mandatory": [],
        }
        for word, wc in words_analysis.items():
            if wc.convergence_tier == 1:
                hitl["skip"].append(word)
            elif wc.convergence_tier in (2, 3):
                hitl["sample_review"].append(word)
            else:
                hitl["mandatory"].append(word)

        return AxisAnalysis(
            axis_id=data.get("axis_id", "unknown"),
            total_words=total,
            total_runs_per_word=max_runs,
            enum_values=data.get("enum_values", []),
            converged_count=converged,
            converged_pct=round(converged / total * 100, 1) if total else 0,
            tier_distribution=tier_dist,
            value_distribution=dict(value_dist),
            words=words_analysis,
            hitl_queue=hitl,
        )

    def pilot_check(self, data: dict) -> PilotResult:
        """Check axis viability from pilot data."""
        analysis = self.analyze_axis(data)

        if analysis.total_words == 0:
            return PilotResult(recommendation="No data. Run pilot first.")

        agreements = [w.agreement_pct for w in analysis.words.values()]
        mean_agr = sum(agreements) / len(agreements)

        # Check for trivial axis
        total_converged = sum(analysis.value_distribution.values())
        single_dominant = False
        if total_converged > 0:
            max_value_count = max(analysis.value_distribution.values())
            if max_value_count / total_converged > 0.90:
                single_dominant = True

        viable = mean_agr > self.pilot_viable_threshold * 100

        if single_dominant:
            rec = (f"CAUTION: >90% of words converge to one value. "
                   f"Axis may be trivial. Check enum design.")
        elif viable:
            rec = (f"VIABLE: mean agreement {mean_agr:.1f}% > "
                   f"{self.pilot_viable_threshold * 100}%. Proceed to full run.")
        else:
            rec = (f"NOT VIABLE: mean agreement {mean_agr:.1f}% < "
                   f"{self.pilot_viable_threshold * 100}%. "
                   f"Axis is distance territory. HITL only.")

        return PilotResult(
            viable=viable,
            mean_agreement=round(mean_agr, 1),
            single_value_dominant=single_dominant,
            recommendation=rec,
            tier_distribution=analysis.tier_distribution,
        )

    def add_run(
        self,
        data: dict,
        run_id: str,
        family: str,
        round_num: int,
        values: dict[str, str],
    ) -> int:
        """Add a run's values to the axis data. Returns count of words updated."""
        enum_values = set(data["enum_values"])
        updated = 0
        invalid = []

        for word, value in values.items():
            if value not in enum_values:
                invalid.append((word, value))
                continue

            if word not in data["words"]:
                data["words"][word] = {"runs": {}}

            data["words"][word]["runs"][run_id] = {
                "value": value,
                "family": family,
                "round": round_num,
            }
            updated += 1

        if run_id not in data.get("runs", []):
            data.setdefault("runs", []).append(run_id)

        if invalid:
            print(f"WARNING: {len(invalid)} invalid enum values skipped:")
            for w, v in invalid[:5]:
                print(f"  {w}: '{v}' not in {data['enum_values']}")
            if len(invalid) > 5:
                print(f"  ... and {len(invalid) - 5} more")

        return updated

    def export_converged(self, data: dict) -> dict:
        """Export converged values for pipeline integration."""
        analysis = self.analyze_axis(data)
        result = {}

        for word, wc in analysis.words.items():
            if not wc.converged:
                continue

            word_data = data["words"].get(word, {})
            runs = word_data.get("runs", {})
            families = list(set(r["family"] for r in runs.values()))

            result[word] = {
                "value": wc.mode,
                "source_type": "estimated",
                "estimation_quality": "converged",
                "convergence_metadata": {
                    "total_runs": wc.total_runs,
                    "families": families,
                    "convergence_tier": wc.convergence_tier,
                    "mode": wc.mode,
                    "agreement_pct": wc.agreement_pct,
                    "family_modes": wc.family_modes,
                    "cross_family_agreement": wc.cross_family_agreement,
                    "distribution": wc.distribution,
                    "protocol": data.get("protocol", "lazarus"),
                },
            }

        return result

    @staticmethod
    def init_axis_data(
        axis_id: str,
        enum_values: list[str],
        description: str = "",
        ordered: bool = False,
        protocol: str = "lazarus",
    ) -> dict:
        """Initialize empty axis data structure."""
        return {
            "axis_id": axis_id,
            "enum_values": enum_values,
            "description": description,
            "ordered": ordered,
            "protocol": protocol,
            "source_type": "estimated",
            "words": {},
            "runs": [],
        }
