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
