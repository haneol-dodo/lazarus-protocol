"""Numeric Convergence Engine.

Runs numeric (0-100 scale) estimation via run-until-convergence.
Convergence = |Δmean| < threshold for min_stable consecutive rounds.

Extracted from Parallax convergence_workflow.py (EXP-005).
"""

import math
from collections import OrderedDict


class NumericConvergence:
    """Engine for numeric convergence analysis.

    All thresholds configurable via constructor. No domain-specific
    references (no CEFR grouping, no P:D prompt).
    """

    def __init__(
        self,
        *,
        threshold: float = 3.0,
        min_stable: int = 2,
        max_rounds: int = 7,
        models: list[str] | None = None,
    ):
        self.threshold = threshold
        self.min_stable = min_stable
        self.max_rounds = max_rounds
        self.models = models or ["haiku", "sonnet", "opus"]
        self.round_size = len(self.models)

    @staticmethod
    def compute_running_stats(values: list[float]) -> dict:
        """Compute mean and SD for a list of values."""
        if not values:
            return {"mean": None, "sd": None, "n": 0}
        n = len(values)
        mean = sum(values) / n
        if n > 1:
            variance = sum((v - mean) ** 2 for v in values) / (n - 1)
            sd = math.sqrt(variance)
        else:
            sd = 0.0
        return {"mean": round(mean, 2), "sd": round(sd, 2), "n": n}

    @staticmethod
    def classify_run_to_round(run_id: str) -> tuple[str, int]:
        """Parse run_id like 'haiku_1' → (model='haiku', instance=1)."""
        parts = run_id.rsplit("_", 1)
        if len(parts) == 2:
            try:
                return parts[0], int(parts[1])
            except ValueError:
                pass
        return run_id, 1

    def organize_by_rounds(self, run_ids: list[str]) -> OrderedDict[int, list[str]]:
        """Organize run IDs into rounds."""
        rounds: dict[int, list[str]] = {}
        for run_id in run_ids:
            _, instance = self.classify_run_to_round(run_id)
            if instance not in rounds:
                rounds[instance] = []
            rounds[instance].append(run_id)
        return OrderedDict(sorted(rounds.items()))

    def check_word_convergence(self, round_deltas: dict[int, float]) -> int | None:
        """Check if deltas have been below threshold for min_stable consecutive rounds.
        Returns the round number where convergence was achieved, or None."""
        consecutive_stable = 0
        for round_num in sorted(round_deltas.keys()):
            if round_deltas[round_num] < self.threshold:
                consecutive_stable += 1
                if consecutive_stable >= self.min_stable:
                    return round_num
            else:
                consecutive_stable = 0
        return None

    def compute_word_convergence(
        self,
        runs: dict[str, float],
        rounds: OrderedDict[int, list[str]],
    ) -> dict:
        """Compute convergence trajectory for a single word.

        Args:
            runs: {run_id: numeric_value} for one word
            rounds: {round_num: [run_ids]} from organize_by_rounds

        Returns dict with round_means, round_deltas, cumulative_stats,
        converged_at, convergence_speed, current_mean, current_sd, total_runs.
        """
        if not runs:
            return {
                "round_means": {},
                "round_deltas": {},
                "cumulative_stats": {},
                "converged_at": None,
                "convergence_speed": None,
                "current_mean": None,
                "current_sd": None,
                "total_runs": 0,
            }

        cumulative_values: list[float] = []
        round_means: dict[int, float | None] = {}
        round_deltas: dict[int, float] = {}
        cumulative_stats: dict[int, dict] = {}

        for round_num, round_run_ids in sorted(rounds.items()):
            for run_id in round_run_ids:
                if run_id in runs:
                    cumulative_values.append(runs[run_id])

            stats = self.compute_running_stats(cumulative_values)
            cumulative_stats[round_num] = stats
            round_means[round_num] = stats["mean"]

            prev_round = round_num - 1
            if prev_round in round_means and round_means[prev_round] is not None:
                delta = abs(round_means[round_num] - round_means[prev_round])
                round_deltas[round_num] = round(delta, 2)

        converged_at = self.check_word_convergence(round_deltas)
        final_stats = cumulative_stats.get(max(cumulative_stats.keys()), {})

        return {
            "round_means": round_means,
            "round_deltas": round_deltas,
            "cumulative_stats": cumulative_stats,
            "converged_at": converged_at,
            "convergence_speed": converged_at if converged_at else None,
            "current_mean": final_stats.get("mean"),
            "current_sd": final_stats.get("sd"),
            "total_runs": len(cumulative_values),
        }

    def add_run(self, data: dict, run_id: str, values: dict[str, float]) -> int:
        """Add a run's values to data. Returns count of words updated.

        Expects data to have 'entities' dict: {group: [entity_dicts]}.
        Each entity has 'word' and optional 'phase2_runs'.
        """
        updated = 0
        for _group, entities in data.get("entities", {}).items():
            for entity in entities:
                word = entity.get("word")
                if word and word in values:
                    if "phase2_runs" not in entity:
                        entity["phase2_runs"] = {}
                    entity["phase2_runs"][run_id] = values[word]
                    updated += 1
        return updated

    def get_all_run_ids(self, data: dict) -> list[str]:
        """Get all unique run IDs across all entities."""
        run_ids: set[str] = set()
        for _group, entities in data.get("entities", {}).items():
            for entity in entities:
                run_ids.update(entity.get("phase2_runs", {}).keys())
        return sorted(run_ids)

    def analyze_all(self, data: dict) -> dict:
        """Full convergence analysis across all words.

        Expects data with 'entities': {group: [entity_dicts]}.
        Returns analysis dict with convergence curve, by_group stats, etc.
        """
        run_ids = self.get_all_run_ids(data)
        rounds = self.organize_by_rounds(run_ids)
        total_rounds = max(rounds.keys()) if rounds else 0

        words_data: dict[str, dict] = {}
        by_group: dict[str, dict] = {}

        for group, entities in data.get("entities", {}).items():
            group_converged = 0
            group_speeds: list[int] = []

            for entity in entities:
                word = entity.get("word", "?")
                runs = dict(entity.get("phase2_runs", {}))
                wc = self.compute_word_convergence(runs, rounds)
                wc["word"] = word
                wc["group"] = group
                words_data[word] = wc

                if wc["converged_at"] is not None:
                    group_converged += 1
                    group_speeds.append(wc["convergence_speed"])

            by_group[group] = {
                "total": len(entities),
                "converged": group_converged,
                "remaining": len(entities) - group_converged,
                "converged_pct": round(group_converged / len(entities) * 100, 1) if entities else 0,
                "mean_speed": round(sum(group_speeds) / len(group_speeds), 1) if group_speeds else None,
            }

        converged_count = sum(1 for w in words_data.values() if w["converged_at"] is not None)
        total_words = len(words_data)

        # Speed buckets
        by_speed: dict = {}
        for word, wc in words_data.items():
            speed = wc["convergence_speed"]
            bucket = speed if speed else "not_converged"
            by_speed.setdefault(bucket, []).append(word)

        # Convergence curve
        convergence_curve: dict[int, float] = {}
        for check_round in sorted(rounds.keys()):
            count = sum(
                1 for wc in words_data.values()
                if wc["converged_at"] is not None and wc["converged_at"] <= check_round
            )
            convergence_curve[check_round] = round(count / total_words * 100, 1) if total_words else 0

        return {
            "total_words": total_words,
            "total_runs_per_word": len(run_ids),
            "total_rounds": total_rounds,
            "run_ids": run_ids,
            "rounds": dict(rounds),
            "threshold": self.threshold,
            "min_stable": self.min_stable,
            "converged_count": converged_count,
            "converged_pct": round(converged_count / total_words * 100, 1) if total_words else 0,
            "remaining_count": total_words - converged_count,
            "words": words_data,
            "by_group": by_group,
            "by_speed": by_speed,
            "convergence_curve": convergence_curve,
        }
