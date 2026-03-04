"""INDEX.md parser and updater for logbook entries."""

import re
from pathlib import Path


def parse_index(index_path: str | Path) -> list[dict]:
    """Parse INDEX.md table into a list of entry records.

    Expects markdown table rows like:
    | 001 | Title | 260301 | phase_name |

    Returns list of dicts with keys: number, title, date, phase.
    """
    path = Path(index_path)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    entries = []

    for line in text.splitlines():
        # Match table rows: | number | title | date | phase |
        m = re.match(
            r"\|\s*(\d{1,4})\s*\|\s*(.+?)\s*\|\s*(\S+)\s*\|\s*(.*?)\s*\|",
            line,
        )
        if m:
            entries.append({
                "number": int(m.group(1)),
                "title": m.group(2).strip(),
                "date": m.group(3).strip(),
                "phase": m.group(4).strip(),
            })

    return entries


def append_to_index(
    index_path: str | Path,
    entry_num: int,
    title: str,
    entry_date: str,
    phase: str = "",
) -> None:
    """Append a new row to the INDEX.md table.

    Creates the file with header if it doesn't exist.
    """
    path = Path(index_path)

    if not path.exists():
        header = (
            "# Logbook Index\n\n"
            "| # | Title | Date | Phase |\n"
            "|---|-------|------|-------|\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header, encoding="utf-8")

    row = f"| {entry_num:03d} | {title} | {entry_date} | {phase} |\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(row)
