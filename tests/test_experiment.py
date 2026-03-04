"""Tests for lazarus.experiment — state transitions, experiment doc validation."""

import tempfile
import unittest
from pathlib import Path

from lazarus.experiment.core import (
    Experiment,
    ExperimentState,
    InvalidTransitionError,
    VALID_TRANSITIONS,
    transition,
)
from lazarus.experiment.tracker import (
    detect_experiment_branch,
    find_experiments,
    validate_experiment_doc,
)


class TestExperimentState(unittest.TestCase):

    def test_all_states_exist(self):
        states = [s.value for s in ExperimentState]
        self.assertIn("design", states)
        self.assertIn("pilot", states)
        self.assertIn("full_run", states)
        self.assertIn("analysis", states)
        self.assertIn("merged", states)
        self.assertIn("abandoned", states)

    def test_terminal_states_have_no_transitions(self):
        self.assertEqual(VALID_TRANSITIONS[ExperimentState.merged], [])
        self.assertEqual(VALID_TRANSITIONS[ExperimentState.abandoned], [])


class TestTransition(unittest.TestCase):

    def _make_exp(self, state=ExperimentState.design):
        return Experiment(
            id="010",
            title="Test",
            branch="exp-010-test",
            state=state,
        )

    def test_design_to_pilot(self):
        exp = self._make_exp(ExperimentState.design)
        new = transition(exp, ExperimentState.pilot)
        self.assertEqual(new.state, ExperimentState.pilot)
        self.assertEqual(new.id, "010")

    def test_pilot_to_full_run(self):
        exp = self._make_exp(ExperimentState.pilot)
        new = transition(exp, ExperimentState.full_run)
        self.assertEqual(new.state, ExperimentState.full_run)

    def test_full_run_to_analysis(self):
        exp = self._make_exp(ExperimentState.full_run)
        new = transition(exp, ExperimentState.analysis)
        self.assertEqual(new.state, ExperimentState.analysis)

    def test_analysis_to_merged(self):
        exp = self._make_exp(ExperimentState.analysis)
        new = transition(exp, ExperimentState.merged)
        self.assertEqual(new.state, ExperimentState.merged)

    def test_any_to_abandoned(self):
        for state in [ExperimentState.design, ExperimentState.pilot,
                      ExperimentState.full_run, ExperimentState.analysis]:
            exp = self._make_exp(state)
            new = transition(exp, ExperimentState.abandoned)
            self.assertEqual(new.state, ExperimentState.abandoned)

    def test_invalid_transition_raises(self):
        exp = self._make_exp(ExperimentState.design)
        with self.assertRaises(InvalidTransitionError):
            transition(exp, ExperimentState.analysis)

    def test_cannot_leave_merged(self):
        exp = self._make_exp(ExperimentState.merged)
        with self.assertRaises(InvalidTransitionError):
            transition(exp, ExperimentState.design)

    def test_cannot_leave_abandoned(self):
        exp = self._make_exp(ExperimentState.abandoned)
        with self.assertRaises(InvalidTransitionError):
            transition(exp, ExperimentState.design)

    def test_pilot_can_return_to_design(self):
        exp = self._make_exp(ExperimentState.pilot)
        new = transition(exp, ExperimentState.design)
        self.assertEqual(new.state, ExperimentState.design)

    def test_analysis_can_return_to_full_run(self):
        exp = self._make_exp(ExperimentState.analysis)
        new = transition(exp, ExperimentState.full_run)
        self.assertEqual(new.state, ExperimentState.full_run)


class TestDetectExperimentBranch(unittest.TestCase):

    def test_standard_branch(self):
        self.assertEqual(detect_experiment_branch("exp-010-convergence"), "010")

    def test_worktree_branch(self):
        self.assertEqual(detect_experiment_branch("worktree-exp-010-convergence"), "010")

    def test_not_experiment(self):
        self.assertIsNone(detect_experiment_branch("main"))
        self.assertIsNone(detect_experiment_branch("feature/auth"))

    def test_different_ids(self):
        self.assertEqual(detect_experiment_branch("exp-005-200survey"), "005")
        self.assertEqual(detect_experiment_branch("exp-001-spectrum"), "001")


class TestFindExperiments(unittest.TestCase):

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(find_experiments(tmpdir), [])

    def test_finds_experiment_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "010_convergence_test.md").write_text(
                "# EXP-010\n\n**Status:** pilot\n"
            )
            (exp_dir / "005_spectrum.md").write_text(
                "# EXP-005\n\n**Status:** merged\n"
            )
            exps = find_experiments(tmpdir)
            self.assertEqual(len(exps), 2)
            self.assertEqual(exps[0].id, "005")
            self.assertEqual(exps[1].id, "010")

    def test_ignores_non_matching_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "README.md").write_text("not an experiment")
            (exp_dir / "utils.py").write_text("# utility")
            exps = find_experiments(tmpdir)
            self.assertEqual(len(exps), 0)


class TestValidateExperimentDoc(unittest.TestCase):

    def test_valid_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "010_test.md").write_text(
                "# EXP-010\n\n"
                "## Objective\nTest something\n\n"
                "## Protocol\nDo steps\n\n"
                "## Status\ndesign\n"
            )
            missing = validate_experiment_doc("010", tmpdir)
            self.assertEqual(missing, [])

    def test_missing_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            (exp_dir / "010_test.md").write_text(
                "# EXP-010\n\nJust some text\n"
            )
            missing = validate_experiment_doc("010", tmpdir)
            self.assertIn("objective", missing)
            self.assertIn("protocol", missing)
            self.assertIn("status", missing)

    def test_no_experiment_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_dir = Path(tmpdir) / "experiments"
            exp_dir.mkdir()
            missing = validate_experiment_doc("099", tmpdir)
            self.assertEqual(len(missing), 1)
            self.assertIn("No experiment document", missing[0])

    def test_no_experiments_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = validate_experiment_doc("010", tmpdir)
            self.assertIn("directory not found", missing[0])


if __name__ == "__main__":
    unittest.main()
