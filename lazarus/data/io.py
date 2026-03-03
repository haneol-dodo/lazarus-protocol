"""I/O utilities for Lazarus protocol data files."""

import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    """Load a JSON file and return its contents."""
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict, ensure_ascii: bool = False):
    """Save data to a JSON file with pretty formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=ensure_ascii)


def parse_csv_output(text: str) -> dict[str, str]:
    """Parse CSV-style LLM output (word,value per line) into a dict.

    Handles common LLM output quirks:
    - Ignores blank lines and comment lines (starting with #)
    - Strips whitespace
    - Skips lines without a comma separator
    """
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",", 1)
        if len(parts) == 2:
            word = parts[0].strip()
            value = parts[1].strip()
            if word:
                result[word] = value
    return result
