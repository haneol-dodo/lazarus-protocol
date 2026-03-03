"""Tests for lazarus.data.sextuple — Sextuple and FacetDefinition."""

import unittest

from lazarus.data.sextuple import Sextuple, FacetDefinition


class TestFacetDefinition(unittest.TestCase):

    def test_position_facet(self):
        f = FacetDefinition(
            name="syllable_count",
            description="Number of syllables",
            facet_type="numeric",
            nature="position",
        )
        self.assertTrue(f.is_position())
        self.assertFalse(f.is_distance())

    def test_distance_facet(self):
        f = FacetDefinition(
            name="difficulty",
            description="Perceived difficulty",
            facet_type="enum",
            values=["easy", "medium", "hard"],
            nature="distance",
        )
        self.assertFalse(f.is_position())
        self.assertTrue(f.is_distance())

    def test_unclassified_default(self):
        f = FacetDefinition(
            name="unknown_axis",
            description="Not yet classified",
            facet_type="enum",
        )
        self.assertFalse(f.is_position())
        self.assertFalse(f.is_distance())
        self.assertEqual(f.nature, "unclassified")

    def test_enum_with_values(self):
        f = FacetDefinition(
            name="register",
            description="Usage register",
            facet_type="enum",
            values=["formal", "neutral", "informal"],
            ordered=True,
        )
        self.assertEqual(f.values, ["formal", "neutral", "informal"])
        self.assertTrue(f.ordered)

    def test_temporal_type(self):
        f = FacetDefinition(
            name="ipa", description="IPA transcription",
            facet_type="string", temporal_type="static",
        )
        self.assertEqual(f.temporal_type, "static")

    def test_parent_facet(self):
        f = FacetDefinition(
            name="culture.ritual_practice",
            description="Observable ritual",
            facet_type="string",
            nature="position",
            parent_facet="culture",
        )
        self.assertEqual(f.parent_facet, "culture")


class TestSextuple(unittest.TestCase):

    def test_position_record(self):
        """Position: (entity, facet, value, t) — 4 fields sufficient."""
        s = Sextuple(
            entity="apple",
            facet="syllable_count",
            value=2,
            source_type="computed",
        )
        self.assertTrue(s.is_complete_position())
        self.assertFalse(s.is_complete_distance())

    def test_distance_record(self):
        """Distance: all 6 fields required."""
        s = Sextuple(
            entity="freedom",
            facet="difficulty",
            value="hard",
            t="2026-03-01T10:00:00",
            observer="theo",
            viewpoint="L1_korean_speaker",
            source_type="observed",
        )
        self.assertTrue(s.is_complete_position())
        self.assertTrue(s.is_complete_distance())

    def test_incomplete_distance(self):
        """Distance record missing observer → incomplete."""
        s = Sextuple(
            entity="freedom",
            facet="difficulty",
            value="hard",
            source_type="observed",
        )
        self.assertTrue(s.is_complete_position())
        self.assertFalse(s.is_complete_distance())

    def test_validate_valid_position(self):
        s = Sextuple(entity="apple", facet="ipa", value="/ˈæp.əl/", source_type="computed")
        issues = s.validate()
        self.assertEqual(issues, [])

    def test_validate_missing_entity(self):
        s = Sextuple(entity="", facet="ipa", value="/test/", source_type="computed")
        issues = s.validate()
        self.assertIn("missing entity", issues)

    def test_validate_missing_value(self):
        s = Sextuple(entity="apple", facet="ipa", value=None, source_type="computed")
        issues = s.validate()
        self.assertIn("missing value", issues)

    def test_validate_invalid_source_type(self):
        s = Sextuple(entity="apple", facet="ipa", value="/test/", source_type="guessed")
        issues = s.validate()
        self.assertIn("invalid source_type: guessed", issues)

    def test_validate_observed_without_provenance(self):
        """C4: observed values must have observer + viewpoint."""
        s = Sextuple(
            entity="apple", facet="difficulty", value="easy",
            source_type="observed",
        )
        issues = s.validate()
        self.assertIn("observed value missing observer (C4)", issues)
        self.assertIn("observed value missing viewpoint (C4)", issues)

    def test_validate_observed_with_provenance(self):
        s = Sextuple(
            entity="apple", facet="difficulty", value="easy",
            source_type="observed",
            observer="theo", viewpoint="coach_diagnostic",
        )
        issues = s.validate()
        self.assertEqual(issues, [])

    def test_validate_with_facet_def_distance(self):
        """Distance facet requires observer/viewpoint (C4)."""
        facet = FacetDefinition(
            name="difficulty", description="test",
            facet_type="enum", values=["easy", "hard"],
            nature="distance",
        )
        s = Sextuple(entity="apple", facet="difficulty", value="easy", source_type="estimated")
        issues = s.validate(facet)
        self.assertIn("distance facet missing observer (C4)", issues)
        self.assertIn("distance facet missing viewpoint (C4)", issues)

    def test_validate_with_facet_def_enum_check(self):
        """Value must be in enum if facet defines values."""
        facet = FacetDefinition(
            name="register", description="test",
            facet_type="enum", values=["formal", "neutral", "informal"],
            nature="position",
        )
        s = Sextuple(
            entity="apple", facet="register", value="slang",
            source_type="computed",
        )
        issues = s.validate(facet)
        self.assertTrue(any("not in enum" in i for i in issues))

    def test_validate_converged_only_for_estimated(self):
        """estimation_quality='converged' only valid for estimated."""
        s = Sextuple(
            entity="apple", facet="ipa", value="/test/",
            source_type="computed",
            estimation_quality="converged",
        )
        issues = s.validate()
        self.assertTrue(any("converged" in i for i in issues))

    def test_validate_converged_estimated_ok(self):
        s = Sextuple(
            entity="apple", facet="imageability", value="high",
            source_type="estimated",
            estimation_quality="converged",
        )
        issues = s.validate()
        self.assertEqual(issues, [])

    def test_default_source_type(self):
        s = Sextuple(entity="apple", facet="test", value="x")
        self.assertEqual(s.source_type, "estimated")


if __name__ == "__main__":
    unittest.main()
