"""Core logbook data structures.

LogbookEntry and LogbookConfig — the building blocks for auto-generated
logbook entries in Lazarus domain projects.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re


@dataclass
class LogbookConfig:
    """Configuration for logbook generation in a domain project."""

    logbook_dir: str = "logbook"
    index_file: str = "INDEX.md"
    voice: dict[str, str] | None = None  # domain-specific voice rules (not enforced)


@dataclass
class LogbookEntry:
    """A single logbook entry."""

    number: int
    title: str
    date: str  # YYMMDD format
    build: str  # e.g. "v1.8.0 (a33eb67) — description"
    trigger: str  # what was being done
    content: str  # main body paragraphs
    voice_rules: dict[str, str] | None = None  # advisory, not enforced
    lens: str = ""
    voice_label: str = ""


def next_entry_number(logbook_dir: str | Path) -> int:
    """Parse INDEX.md to find the next available entry number.

    Scans for patterns like '| 001 |' or '| 42 |' in the index table.
    Returns max + 1, or 1 if no entries found.
    """
    index_path = Path(logbook_dir) / "INDEX.md"
    if not index_path.exists():
        return 1

    text = index_path.read_text(encoding="utf-8")
    # Match entry numbers in markdown table rows: | 001 | or | 42 |
    numbers = re.findall(r"\|\s*(\d{1,4})\s*\|", text)
    if not numbers:
        return 1

    return max(int(n) for n in numbers) + 1


def format_entry(entry: LogbookEntry) -> str:
    """Render a LogbookEntry to markdown string."""
    lines = [
        f"# {entry.number:03d} — {entry.title}",
        "",
        f"> **Date:** {entry.date}",
        f"> **Build:** {entry.build}",
        f"> **Trigger:** {entry.trigger}",
    ]

    if entry.lens:
        lines.append(f"> **Lens:** {entry.lens}")
    if entry.voice_label:
        lines.append(f"> **Voice:** {entry.voice_label}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(entry.content)
    lines.append("")

    return "\n".join(lines)
