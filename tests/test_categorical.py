"""Tests for lazarus.convergence.categorical — CategoricalConvergence engine."""

import unittest

from lazarus.convergence.categorical import CategoricalConvergence
from lazarus.convergence.types import WordConvergenceResult, AxisAnalysis, PilotResult


class TestWordConvergence(unittest.TestCase):
    """Test compute_word_convergence on synthetic data."""

    def setUp(self):
        self.cc = CategoricalConvergence(
            min_agreement=0.70,
            min_stable_rounds=2,
            families=["claude", "openai", "google"],
            runs_per_round=6,
        )
        self.enum_values = ["high", "medium", "low"]

    def test_empty_word(self):
        wc = self.cc.compute_word_convergence("apple", {}, self.enum_values)
        self.assertIsInstance(wc, WordConvergenceResult)
        self.assertEqual(wc.word, "apple")
        self.assertEqual(wc.total_runs, 0)
        self.assertFalse(wc.converged)
        self.assertEqual(wc.convergence_tier, 4)

    def test_perfect_agreement(self):
        """6 runs all saying 'high' across 2 rounds → converged Tier 1."""
        word_data = {"runs": {
            "claude_1": {"value": "high", "family": "claude", "round": 1},
            "openai_1": {"value": "high", "family": "openai", "round": 1},
            "google_1": {"value": "high", "family": "google", "round": 1},
            "claude_2": {"value": "high", "family": "claude", "round": 2},
            "openai_2": {"value": "high", "family": "openai", "round": 2},
            "google_2": {"value": "high", "family": "google", "round": 2},
        }}
        wc = self.cc.compute_word_convergence("salt", word_data, self.enum_values)
        self.assertTrue(wc.converged)
        self.assertEqual(wc.mode, "high")
        self.assertEqual(wc.agreement_pct, 100.0)
        self.assertEqual(wc.convergence_tier, 1)
        self.assertTrue(wc.cross_family_agreement)

    def test_majority_agreement_converges(self):
        """5/6 agree → 83.3% agreement → Tier 2 (>=80%)."""
        word_data = {"runs": {
            "claude_1": {"value": "medium", "family": "claude", "round": 1},
            "openai_1": {"value": "medium", "family": "openai", "round": 1},
            "google_1": {"value": "low", "family": "google", "round": 1},
            "claude_2": {"value": "medium", "family": "claude", "round": 2},
            "openai_2": {"value": "medium", "family": "openai", "round": 2},
            "google_2": {"value": "medium", "family": "google", "round": 2},
        }}
        wc = self.cc.compute_word_convergence("tree", word_data, self.enum_values)
        self.assertTrue(wc.converged)
        self.assertEqual(wc.mode, "medium")
        self.assertAlmostEqual(wc.agreement_pct, 83.3, places=1)
        self.assertEqual(wc.convergence_tier, 2)

    def test_below_threshold_no_convergence(self):
        """3/6 agree → 50% < 70% threshold → not converged."""
        word_data = {"runs": {
            "claude_1": {"value": "high", "family": "claude", "round": 1},
            "openai_1": {"value": "medium", "family": "openai", "round": 1},
            "google_1": {"value": "low", "family": "google", "round": 1},
            "claude_2": {"value": "high", "family": "claude", "round": 2},
            "openai_2": {"value": "medium", "family": "openai", "round": 2},
            "google_2": {"value": "high", "family": "google", "round": 2},
        }}
        wc = self.cc.compute_word_convergence("freedom", word_data, self.enum_values)
        self.assertFalse(wc.converged)
        self.assertEqual(wc.convergence_tier, 4)

    def test_mode_unstable_no_convergence(self):
        """Mode changes between rounds → not converged even if agreement high enough."""
        word_data = {"runs": {
            "claude_1": {"value": "high", "family": "claude", "round": 1},
            "openai_1": {"value": "high", "family": "openai", "round": 1},
            "google_1": {"value": "high", "family": "google", "round": 1},
            "claude_2": {"value": "low", "family": "claude", "round": 2},
            "openai_2": {"value": "low", "family": "openai", "round": 2},
            "google_2": {"value": "low", "family": "google", "round": 2},
        }}
        wc = self.cc.compute_word_convergence("best", word_data, self.enum_values)
        # 3/6 = 50% for each, mode is whichever counter picks first
        # Even if one mode = 50%, it's < 70% threshold → not converged
        self.assertFalse(wc.converged)

    def test_cross_family_disagreement(self):
        """Different families have different modes."""
        word_data = {"runs": {
            "claude_1": {"value": "high", "family": "claude", "round": 1},
            "claude_2": {"value": "high", "family": "claude", "round": 2},
            "openai_1": {"value": "low", "family": "openai", "round": 1},
            "openai_2": {"value": "low", "family": "openai", "round": 2},
            "google_1": {"value": "high", "family": "google", "round": 1},
            "google_2": {"value": "high", "family": "google", "round": 2},
        }}
        wc = self.cc.compute_word_convergence("argue", word_data, self.enum_values)
        self.assertFalse(wc.cross_family_agreement)


class TestAnalyzeAxis(unittest.TestCase):
    """Test analyze_axis with synthetic 3-word axis."""

    def setUp(self):
        self.cc = CategoricalConvergence(
            min_agreement=0.70,
            min_stable_rounds=2,
        )

    def _make_data(self):
        return {
            "axis_id": "test.axis",
            "enum_values": ["alpha", "beta", "gamma"],
            "words": {
                "word_a": {"runs": {
                    "r1": {"value": "alpha", "family": "claude", "round": 1},
                    "r2": {"value": "alpha", "family": "openai", "round": 1},
                    "r3": {"value": "alpha", "family": "google", "round": 1},
                    "r4": {"value": "alpha", "family": "claude", "round": 2},
                    "r5": {"value": "alpha", "family": "openai", "round": 2},
                    "r6": {"value": "alpha", "family": "google", "round": 2},
                }},
                "word_b": {"runs": {
                    "r1": {"value": "beta", "family": "claude", "round": 1},
                    "r2": {"value": "beta", "family": "openai", "round": 1},
                    "r3": {"value": "gamma", "family": "google", "round": 1},
                    "r4": {"value": "beta", "family": "claude", "round": 2},
                    "r5": {"value": "beta", "family": "openai", "round": 2},
                    "r6": {"value": "beta", "family": "google", "round": 2},
                }},
                "word_c": {"runs": {
                    "r1": {"value": "alpha", "family": "claude", "round": 1},
                    "r2": {"value": "beta", "family": "openai", "round": 1},
                    "r3": {"value": "gamma", "family": "google", "round": 1},
                    "r4": {"value": "beta", "family": "claude", "round": 2},
                    "r5": {"value": "alpha", "family": "openai", "round": 2},
                    "r6": {"value": "gamma", "family": "google", "round": 2},
                }},
            },
        }

    def test_axis_analysis_structure(self):
        data = self._make_data()
        analysis = self.cc.analyze_axis(data)
        self.assertIsInstance(analysis, AxisAnalysis)
        self.assertEqual(analysis.axis_id, "test.axis")
        self.assertEqual(analysis.total_words, 3)
        self.assertEqual(analysis.enum_values, ["alpha", "beta", "gamma"])

    def test_convergence_counts(self):
        data = self._make_data()
        analysis = self.cc.analyze_axis(data)
        # word_a: 100% alpha → converged Tier 1
        # word_b: 83.3% beta → converged Tier 2
        # word_c: evenly split → not converged
        self.assertEqual(analysis.converged_count, 2)
        self.assertAlmostEqual(analysis.converged_pct, 66.7, places=1)

    def test_tier_distribution(self):
        data = self._make_data()
        analysis = self.cc.analyze_axis(data)
        self.assertEqual(analysis.tier_distribution[1], 1)  # word_a
        self.assertEqual(analysis.tier_distribution[2], 1)  # word_b
        self.assertEqual(analysis.tier_distribution[4], 1)  # word_c

    def test_hitl_queue(self):
        data = self._make_data()
        analysis = self.cc.analyze_axis(data)
        self.assertIn("word_a", analysis.hitl_queue["skip"])
        self.assertIn("word_b", analysis.hitl_queue["sample_review"])
        self.assertIn("word_c", analysis.hitl_queue["mandatory"])

    def test_value_distribution(self):
        data = self._make_data()
        analysis = self.cc.analyze_axis(data)
        self.assertEqual(analysis.value_distribution["alpha"], 1)
        self.assertEqual(analysis.value_distribution["beta"], 1)


class TestPilotCheck(unittest.TestCase):

    def setUp(self):
        self.cc = CategoricalConvergence(
            min_agreement=0.70,
            min_stable_rounds=2,
            pilot_viable_threshold=0.40,
        )

    def test_viable_pilot(self):
        """Mean agreement > 40% → viable."""
        data = {
            "axis_id": "test.pilot",
            "enum_values": ["a", "b"],
            "words": {
                "w1": {"runs": {
                    "r1": {"value": "a", "family": "claude", "round": 1},
                    "r2": {"value": "a", "family": "openai", "round": 1},
                    "r3": {"value": "a", "family": "google", "round": 1},
                    "r4": {"value": "a", "family": "claude", "round": 2},
                    "r5": {"value": "a", "family": "openai", "round": 2},
                    "r6": {"value": "a", "family": "google", "round": 2},
                }},
                "w2": {"runs": {
                    "r1": {"value": "b", "family": "claude", "round": 1},
                    "r2": {"value": "b", "family": "openai", "round": 1},
                    "r3": {"value": "a", "family": "google", "round": 1},
                    "r4": {"value": "b", "family": "claude", "round": 2},
                    "r5": {"value": "b", "family": "openai", "round": 2},
                    "r6": {"value": "b", "family": "google", "round": 2},
                }},
            },
        }
        result = self.cc.pilot_check(data)
        self.assertIsInstance(result, PilotResult)
        self.assertTrue(result.viable)
        self.assertGreater(result.mean_agreement, 40)

    def test_empty_pilot(self):
        data = {"axis_id": "test.empty", "enum_values": ["a", "b"], "words": {}}
        result = self.cc.pilot_check(data)
        self.assertFalse(result.viable)
        self.assertIn("No data", result.recommendation)

    def test_single_value_dominant_warning(self):
        """If >90% converge to one value, flag as potentially trivial."""
        data = {
            "axis_id": "test.trivial",
            "enum_values": ["yes", "no"],
            "words": {},
        }
        # 10 words all converging to "yes"
        for i in range(10):
            data["words"][f"w{i}"] = {"runs": {
                "r1": {"value": "yes", "family": "claude", "round": 1},
                "r2": {"value": "yes", "family": "openai", "round": 1},
                "r3": {"value": "yes", "family": "google", "round": 1},
                "r4": {"value": "yes", "family": "claude", "round": 2},
                "r5": {"value": "yes", "family": "openai", "round": 2},
                "r6": {"value": "yes", "family": "google", "round": 2},
            }}
        result = self.cc.pilot_check(data)
        self.assertTrue(result.single_value_dominant)
        self.assertIn("trivial", result.recommendation.lower())


class TestAddRun(unittest.TestCase):

    def setUp(self):
        self.cc = CategoricalConvergence()

    def test_add_run_updates_words(self):
        data = CategoricalConvergence.init_axis_data("test", ["a", "b", "c"])
        count = self.cc.add_run(data, "run1", "claude", 1, {"word1": "a", "word2": "b"})
        self.assertEqual(count, 2)
        self.assertEqual(data["words"]["word1"]["runs"]["run1"]["value"], "a")
        self.assertEqual(data["words"]["word1"]["runs"]["run1"]["family"], "claude")
        self.assertEqual(data["words"]["word1"]["runs"]["run1"]["round"], 1)
        self.assertIn("run1", data["runs"])

    def test_add_run_rejects_invalid_values(self):
        data = CategoricalConvergence.init_axis_data("test", ["a", "b"])
        count = self.cc.add_run(data, "run1", "claude", 1, {"word1": "invalid"})
        self.assertEqual(count, 0)
        self.assertNotIn("word1", data["words"])


class TestInitAxisData(unittest.TestCase):

    def test_structure(self):
        data = CategoricalConvergence.init_axis_data(
            "gap09.imageability",
            ["high", "medium", "low", "abstract"],
            description="Mental image ease",
            ordered=True,
        )
        self.assertEqual(data["axis_id"], "gap09.imageability")
        self.assertEqual(data["enum_values"], ["high", "medium", "low", "abstract"])
        self.assertEqual(data["description"], "Mental image ease")
        self.assertTrue(data["ordered"])
        self.assertEqual(data["source_type"], "estimated")
        self.assertEqual(data["words"], {})
        self.assertEqual(data["runs"], [])
        self.assertEqual(data["protocol"], "lazarus")


class TestExportConverged(unittest.TestCase):

    def setUp(self):
        self.cc = CategoricalConvergence(
            min_agreement=0.70,
            min_stable_rounds=2,
        )

    def test_export_includes_metadata(self):
        data = CategoricalConvergence.init_axis_data("test", ["a", "b"])
        # Add 6 runs all agreeing on "a" across 2 rounds
        for i, family in enumerate(["claude", "openai", "google"]):
            for rnd in [1, 2]:
                run_id = f"{family}_{rnd}"
                self.cc.add_run(data, run_id, family, rnd, {"word1": "a"})

        exported = self.cc.export_converged(data)
        self.assertIn("word1", exported)
        self.assertEqual(exported["word1"]["value"], "a")
        self.assertEqual(exported["word1"]["source_type"], "estimated")
        self.assertEqual(exported["word1"]["estimation_quality"], "converged")
        meta = exported["word1"]["convergence_metadata"]
        self.assertEqual(meta["mode"], "a")
        self.assertEqual(meta["agreement_pct"], 100.0)
        self.assertTrue(meta["cross_family_agreement"])


if __name__ == "__main__":
    unittest.main()
