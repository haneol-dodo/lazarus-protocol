"""Logbook entry generation from git diffs.

Classifies commits as meaningful/trivial and generates logbook drafts.
"""

import re
from datetime import date

from .core import LogbookConfig, LogbookEntry, next_entry_number


# File path patterns that indicate meaningful changes
MEANINGFUL_PATTERNS: list[tuple[str, str]] = [
    (r"enums?/", "constraint"),
    (r"engine/", "feature"),
    (r"experiments?/", "discovery"),
    (r"pipeline", "feature"),
    (r"audit", "constraint"),
    (r"constraints?", "constraint"),
    (r"CLAUDE\.md", "architecture"),
    (r"_schema/", "architecture"),
    (r"references?/", "architecture"),
    (r"bridge_", "architecture"),
    (r"hooks/", "constraint"),
]

# Patterns that indicate trivial changes (skip logbook)
TRIVIAL_PATTERNS: list[str] = [
    r"\.md$",  # Only if no other meaningful files
    r"README",
    r"\.gitignore$",
    r"requirements\.txt$",
    r"pyproject\.toml$",
    r"package\.json$",
    r"\.lock$",
]

# Diff content patterns for trivial changes
TRIVIAL_DIFF_PATTERNS: list[str] = [
    r"^[-+]\s+#",  # comment-only changes (space before # to avoid matching markdown headings)
    r"^[-+]\s*$",  # blank line changes
    r'^\s*[-+]\s*["\']?version["\']?\s*[:=]',  # version bumps only
]


def _extract_changed_files(diff_text: str) -> list[str]:
    """Extract file paths from a git diff."""
    files = re.findall(r"^diff --git a/(.+?) b/", diff_text, re.MULTILINE)
    if not files:
        # Fallback: try --name-only style
        files = [
            line.strip()
            for line in diff_text.splitlines()
            if line.strip() and not line.startswith(("diff ", "index ", "---", "+++", "@@", "+", "-", " "))
        ]
    return files


def _is_trivial_diff_content(diff_text: str) -> bool:
    """Check if the actual diff content is trivial (comments, blanks, formatting)."""
    # Extract actual change lines (+ or - prefixed, excluding file headers)
    change_lines = []
    for line in diff_text.splitlines():
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---", "diff ")):
            change_lines.append(line)

    if not change_lines:
        return True

    # If all change lines match trivial patterns, it's trivial
    for line in change_lines:
        is_trivial = False
        for pattern in TRIVIAL_DIFF_PATTERNS:
            if re.match(pattern, line):
                is_trivial = True
                break
        if not is_trivial:
            return False

    return True


def classify_commit(diff_text: str) -> str | None:
    """Classify a commit based on its diff.

    Returns category string or None if trivial.
    Categories: feature, constraint, architecture, milestone, bugfix, discovery
    """
    if not diff_text or not diff_text.strip():
        return None

    files = _extract_changed_files(diff_text)
    if not files:
        return None

    # Check for meaningful file patterns
    categories_found: set[str] = set()
    has_meaningful = False

    for fpath in files:
        for pattern, category in MEANINGFUL_PATTERNS:
            if re.search(pattern, fpath):
                categories_found.add(category)
                has_meaningful = True
                break

    if not has_meaningful:
        return None

    # Check if diff content itself is trivial despite touching meaningful dirs
    if _is_trivial_diff_content(diff_text):
        return None

    # Priority: constraint > architecture > feature > discovery
    if "constraint" in categories_found:
        return "constraint"
    if "architecture" in categories_found:
        return "architecture"
    if "discovery" in categories_found:
        return "discovery"
    return "feature"


def is_meaningful_commit(diff_text: str) -> bool:
    """Detect if a commit warrants a logbook entry."""
    return classify_commit(diff_text) is not None


def generate_draft(
    diff_text: str,
    commit_msg: str,
    config: LogbookConfig,
) -> LogbookEntry:
    """Produce a logbook draft from a git diff.

    The draft provides structure only — voice and content are
    telescope territory, not calculator. The human refines.
    """
    category = classify_commit(diff_text) or "feature"
    files = _extract_changed_files(diff_text)
    entry_num = next_entry_number(config.logbook_dir)
    today = date.today().strftime("%y%m%d")

    # Build a title from commit message
    title = commit_msg.split("\n")[0].strip()
    if len(title) > 80:
        title = title[:77] + "..."

    # Summarize changed files for the content body
    file_summary = "\n".join(f"- `{f}`" for f in files[:10])
    if len(files) > 10:
        file_summary += f"\n- ... and {len(files) - 10} more files"

    content = (
        f"[DRAFT — Human review required]\n\n"
        f"**Category:** {category}\n\n"
        f"**Changed files:**\n{file_summary}\n\n"
        f"**Commit message:** {commit_msg}\n\n"
        f"[TODO: Describe what changed, why it matters, what it connects to]\n"
    )

    return LogbookEntry(
        number=entry_num,
        title=title,
        date=today,
        build=f"(see git log for commit hash)",
        trigger=f"Commit: {commit_msg.split(chr(10))[0][:60]}",
        content=content,
        voice_rules=config.voice,
    )
