"""Tests for lazarus.logbook — entry generation, index parsing, meaningful commit detection."""

import tempfile
import unittest
from pathlib import Path

from lazarus.logbook.core import (
    LogbookConfig,
    LogbookEntry,
    format_entry,
    next_entry_number,
)
from lazarus.logbook.generator import (
    classify_commit,
    generate_draft,
    is_meaningful_commit,
)
from lazarus.logbook.index import append_to_index, parse_index


class TestLogbookEntry(unittest.TestCase):

    def test_format_entry_basic(self):
        entry = LogbookEntry(
            number=42,
            title="Test Entry",
            date="260304",
            build="v1.0 (abc1234) — test",
            trigger="Unit test",
            content="This is the content.",
        )
        text = format_entry(entry)
        self.assertIn("# 042 — Test Entry", text)
        self.assertIn("**Date:** 260304", text)
        self.assertIn("**Build:** v1.0 (abc1234) — test", text)
        self.assertIn("**Trigger:** Unit test", text)
        self.assertIn("This is the content.", text)

    def test_format_entry_with_lens_and_voice(self):
        entry = LogbookEntry(
            number=1,
            title="First",
            date="260101",
            build="v0.1",
            trigger="init",
            content="Body.",
            lens="UX Research",
            voice_label="TEDx casual",
        )
        text = format_entry(entry)
        self.assertIn("**Lens:** UX Research", text)
        self.assertIn("**Voice:** TEDx casual", text)

    def test_format_entry_number_padding(self):
        entry = LogbookEntry(
            number=1, title="T", date="d", build="b", trigger="t", content="c",
        )
        text = format_entry(entry)
        self.assertIn("# 001 — T", text)


class TestNextEntryNumber(unittest.TestCase):

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(next_entry_number(tmpdir), 1)

    def test_no_index_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(next_entry_number(tmpdir), 1)

    def test_parses_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Path(tmpdir) / "INDEX.md"
            index.write_text(
                "| # | Title | Date | Phase |\n"
                "|---|-------|------|-------|\n"
                "| 001 | First | 260101 | init |\n"
                "| 002 | Second | 260102 | build |\n"
                "| 010 | Tenth | 260110 | build |\n"
            )
            self.assertEqual(next_entry_number(tmpdir), 11)

    def test_single_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Path(tmpdir) / "INDEX.md"
            index.write_text("| 005 | Only | 260105 | x |\n")
            self.assertEqual(next_entry_number(tmpdir), 6)


class TestClassifyCommit(unittest.TestCase):

    def test_enum_change_is_constraint(self):
        diff = (
            "diff --git a/enums/gap01.json b/enums/gap01.json\n"
            "--- a/enums/gap01.json\n"
            "+++ b/enums/gap01.json\n"
            "@@ -1 +1 @@\n"
            '-  "value": "old"\n'
            '+  "value": "new"\n'
        )
        self.assertEqual(classify_commit(diff), "constraint")

    def test_engine_change_is_feature(self):
        diff = (
            "diff --git a/engine/pipeline.py b/engine/pipeline.py\n"
            "--- a/engine/pipeline.py\n"
            "+++ b/engine/pipeline.py\n"
            "@@ -10 +10 @@\n"
            "-def old_func():\n"
            "+def new_func():\n"
        )
        self.assertEqual(classify_commit(diff), "feature")

    def test_experiment_change_is_discovery(self):
        diff = (
            "diff --git a/experiments/010_test.md b/experiments/010_test.md\n"
            "--- a/experiments/010_test.md\n"
            "+++ b/experiments/010_test.md\n"
            "@@ -1 +1 @@\n"
            "-# old\n"
            "+# new\n"
        )
        self.assertEqual(classify_commit(diff), "discovery")

    def test_empty_diff_is_none(self):
        self.assertIsNone(classify_commit(""))
        self.assertIsNone(classify_commit("   "))

    def test_trivial_diff_is_none(self):
        # Comment-only changes in meaningful dir
        diff = (
            "diff --git a/engine/test.py b/engine/test.py\n"
            "--- a/engine/test.py\n"
            "+++ b/engine/test.py\n"
            "@@ -1 +1 @@\n"
            "-  # old comment\n"
            "+  # new comment\n"
        )
        self.assertIsNone(classify_commit(diff))

    def test_non_meaningful_file(self):
        diff = (
            "diff --git a/README.md b/README.md\n"
            "--- a/README.md\n"
            "+++ b/README.md\n"
            "@@ -1 +1 @@\n"
            "-old text\n"
            "+new text\n"
        )
        self.assertIsNone(classify_commit(diff))


class TestIsMeaningfulCommit(unittest.TestCase):

    def test_meaningful(self):
        diff = (
            "diff --git a/engine/new_module.py b/engine/new_module.py\n"
            "+++ b/engine/new_module.py\n"
            "@@ -0,0 +1 @@\n"
            "+def new_function(): pass\n"
        )
        self.assertTrue(is_meaningful_commit(diff))

    def test_not_meaningful(self):
        self.assertFalse(is_meaningful_commit(""))


class TestGenerateDraft(unittest.TestCase):

    def test_generates_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogbookConfig(logbook_dir=tmpdir)
            diff = (
                "diff --git a/engine/gap01.py b/engine/gap01.py\n"
                "+++ b/engine/gap01.py\n"
                "@@ -0,0 +1 @@\n"
                "+def compute(): pass\n"
            )
            entry = generate_draft(diff, "Add gap01 module", config)
            self.assertEqual(entry.number, 1)
            self.assertEqual(entry.title, "Add gap01 module")
            self.assertIn("DRAFT", entry.content)
            self.assertIn("engine/gap01.py", entry.content)


class TestParseIndex(unittest.TestCase):

    def test_parse_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "INDEX.md"
            self.assertEqual(parse_index(path), [])

    def test_parse_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "INDEX.md"
            path.write_text(
                "| # | Title | Date | Phase |\n"
                "|---|-------|------|-------|\n"
                "| 001 | First Entry | 260101 | init |\n"
                "| 002 | Second | 260102 | build |\n"
            )
            entries = parse_index(path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["number"], 1)
            self.assertEqual(entries[0]["title"], "First Entry")
            self.assertEqual(entries[1]["number"], 2)
            self.assertEqual(entries[1]["phase"], "build")


class TestAppendToIndex(unittest.TestCase):

    def test_creates_file_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "INDEX.md"
            append_to_index(path, 1, "First", "260101", "init")
            self.assertTrue(path.exists())
            text = path.read_text()
            self.assertIn("| 001 | First | 260101 | init |", text)
            self.assertIn("# | Title", text)  # header

    def test_appends_to_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "INDEX.md"
            path.write_text(
                "| # | Title | Date | Phase |\n"
                "|---|-------|------|-------|\n"
                "| 001 | First | 260101 | init |\n"
            )
            append_to_index(path, 2, "Second", "260102", "build")
            entries = parse_index(path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[1]["number"], 2)


if __name__ == "__main__":
    unittest.main()
