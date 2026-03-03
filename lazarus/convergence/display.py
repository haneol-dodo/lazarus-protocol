"""Display functions for convergence analysis results.

Extracted from Parallax 010_categorical_convergence.py and convergence_workflow.py.
Parameterized: takes AxisAnalysis / analysis dicts, no hardcoded domain references.
"""

from .types import AxisAnalysis


# ---------------------------------------------------------------------------
# Categorical display
# ---------------------------------------------------------------------------

def print_categorical_analysis(
    analysis: AxisAnalysis,
    min_stable_rounds: int = 2,
    min_agreement: float = 0.70,
) -> None:
    """Print categorical convergence analysis to stdout."""
    print("=" * 70)
    print(f"CATEGORICAL CONVERGENCE: {analysis.axis_id}")
    print("=" * 70)
    print(f"Total words:     {analysis.total_words}")
    print(f"Max runs/word:   {analysis.total_runs_per_word}")
    print(f"Enum values:     {', '.join(analysis.enum_values)}")
    print(f"Convergence:     mode stable {min_stable_rounds} rounds + "
          f"agreement >= {min_agreement * 100:.0f}%")
    print()

    td = analysis.tier_distribution
    total = analysis.total_words
    print("TIER DISTRIBUTION:")
    for tier in [1, 2, 3, 4]:
        n = td.get(tier, 0)
        pct = n / total * 100 if total else 0
        bar = "#" * int(pct / 2)
        label = {
            1: "Strong (>=90%)",
            2: "Good   (>=80%)",
            3: "Weak   (>=70%)",
            4: "None   (<70%) ",
        }[tier]
        print(f"  Tier {tier} {label}: {n:4d} ({pct:5.1f}%) {bar}")
    print()

    print("VALUE DISTRIBUTION (converged words):")
    vd = analysis.value_distribution
    for val in analysis.enum_values:
        n = vd.get(val, 0)
        print(f"  {val:<20s}: {n}")
    print()

    print(f"CONVERGED: {analysis.converged_count}/{total} "
          f"({analysis.converged_pct}%)")
    print()

    hq = analysis.hitl_queue
    print("HITL QUEUE:")
    print(f"  Skip (Tier 1):      {len(hq.get('skip', []))} words")
    print(f"  Sample review (2-3): {len(hq.get('sample_review', []))} words")
    print(f"  Mandatory (Tier 4):  {len(hq.get('mandatory', []))} words")


def print_categorical_remaining(analysis: AxisAnalysis) -> None:
    """Print unconverged words for a categorical axis."""
    remaining = {
        w: wc for w, wc in analysis.words.items()
        if not wc.converged
    }

    if not remaining:
        print("All words converged!")
        return

    print(f"REMAINING: {len(remaining)} words not yet converged")
    print(f"{'Word':<20s} {'Runs':>4} {'Mode':<15s} {'Agr%':>5} {'Families':>10}")
    print("-" * 60)

    for word, wc in sorted(remaining.items(), key=lambda x: x[1].agreement_pct):
        fam_str = ",".join(sorted(wc.family_modes.keys()))
        print(f"{word:<20s} {wc.total_runs:>4} "
              f"{wc.mode or '?':<15s} {wc.agreement_pct:>5.1f} "
              f"{fam_str:>10}")


def print_categorical_report(
    analysis: AxisAnalysis,
    min_stable_rounds: int = 2,
    min_agreement: float = 0.70,
) -> None:
    """Full detailed categorical report."""
    print_categorical_analysis(analysis, min_stable_rounds, min_agreement)
    print()
    print("=" * 70)
    print("PER-WORD DETAIL")
    print("=" * 70)

    by_tier: dict[int, list] = {1: [], 2: [], 3: [], 4: []}
    for word, wc in sorted(analysis.words.items()):
        by_tier[wc.convergence_tier].append((word, wc))

    for tier in [1, 2, 3, 4]:
        words = by_tier[tier]
        if not words:
            continue
        tier_label = {
            1: "TIER 1 — Strong consensus (>=90%)",
            2: "TIER 2 — Good consensus (>=80%)",
            3: "TIER 3 — Weak consensus (>=70%)",
            4: "TIER 4 — No convergence (<70%)",
        }[tier]
        print(f"\n--- {tier_label}: {len(words)} words ---")

        for word, wc in words:
            dist_str = " ".join(
                f"{v}:{wc.distribution.get(v, 0)}"
                for v in analysis.enum_values
            )
            cf = "CF" if wc.cross_family_agreement else "!CF"
            print(f"  {word:<20s} mode={wc.mode:<12s} "
                  f"agr={wc.agreement_pct:>5.1f}% "
                  f"[{dist_str}] {cf}")


# ---------------------------------------------------------------------------
# Numeric display
# ---------------------------------------------------------------------------

def print_numeric_analysis(analysis: dict, round_size: int = 3) -> None:
    """Print numeric convergence analysis to stdout."""
    print("=" * 70)
    print("ITERATION CONVERGENCE ANALYSIS")
    print("=" * 70)
    print(f"Total words:    {analysis['total_words']}")
    print(f"Runs per word:  {analysis['total_runs_per_word']}")
    print(f"Total rounds:   {analysis['total_rounds']}")
    print(f"Run IDs:        {', '.join(analysis['run_ids'])}")
    print(f"Threshold:      Δmean < {analysis['threshold']} "
          f"for {analysis['min_stable']} consecutive rounds")
    print()

    print("ROUND STRUCTURE:")
    for round_num, run_ids in analysis["rounds"].items():
        total_at = round_num * round_size
        print(f"  Round {round_num} (runs {(round_num-1)*round_size+1}-{total_at}): "
              f"{', '.join(run_ids)}")
    print()

    print("CONVERGENCE CURVE:")
    for round_num, pct in analysis["convergence_curve"].items():
        bar_filled = int(pct / 2)
        bar = "#" * bar_filled + "." * (50 - bar_filled)
        total_runs = round_num * round_size
        print(f"  Run {total_runs:2d} (Round {round_num}): {bar} {pct}%")
    print()

    print(f"CONVERGED:  {analysis['converged_count']}/{analysis['total_words']} "
          f"({analysis['converged_pct']}%)")
    print(f"REMAINING:  {analysis['remaining_count']}")
    print()

    if "by_group" in analysis:
        print("BY GROUP:")
        for group, bg in sorted(analysis["by_group"].items()):
            speed_str = f" | mean speed: round {bg['mean_speed']}" if bg["mean_speed"] else ""
            print(f"  {group}: {bg['converged']}/{bg['total']} converged "
                  f"({bg['converged_pct']}%){speed_str}")
        print()

    print("CONVERGENCE SPEED DISTRIBUTION:")
    for bucket in sorted(analysis["by_speed"].keys(), key=lambda x: (isinstance(x, str), x)):
        words = analysis["by_speed"][bucket]
        label = f"Round {bucket}" if bucket != "not_converged" else "Not converged"
        print(f"  {label}: {len(words)} words")
        examples = words[:10]
        if len(words) > 10:
            print(f"    {', '.join(examples)}, ... (+{len(words) - 10} more)")
        else:
            print(f"    {', '.join(examples)}")
    print()


def print_numeric_remaining(analysis: dict) -> None:
    """Print unconverged words for a numeric axis."""
    remaining = {
        word: wc for word, wc in analysis["words"].items()
        if wc["converged_at"] is None
    }

    if not remaining:
        print("All words converged!")
        return

    sorted_words = sorted(remaining.items(), key=lambda x: -(x[1]["current_sd"] or 0))

    print(f"REMAINING: {len(remaining)} words not yet converged")
    print(f"{'Word':<20} {'Group':<6} {'Mean':>6} {'SD':>6} {'Runs':>4}  Trajectory")
    print("-" * 75)

    for word, wc in sorted_words:
        trajectory = " -> ".join(
            f"{v:.0f}" for k, v in sorted(wc["round_means"].items())
            if v is not None
        )
        group = wc.get("group", "?")
        print(f"{word:<20} {group:<6} "
              f"{wc['current_mean']:>6.1f} {wc['current_sd']:>6.1f} "
              f"{wc['total_runs']:>4}  {trajectory}")
