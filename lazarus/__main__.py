"""Lazarus Protocol CLI.

Usage:
    python -m lazarus init <project-name> [--path <dir>]
"""

import argparse
import os
import sys
from pathlib import Path
from string import Template


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def cmd_init(args):
    """Scaffold a new Lazarus domain project."""
    name = args.project_name
    slug = name.lower().replace(" ", "_").replace("-", "_")
    target = Path(args.path) if args.path else Path.cwd() / name

    if target.exists() and any(target.iterdir()):
        print(f"ERROR: {target} already exists and is not empty.", file=sys.stderr)
        sys.exit(1)

    # Substitution map
    subs = {
        "DOMAIN_NAME": name,
        "domain_name": slug,
        "domain_module": slug,
        "example_facet_id": "facet.example",
    }

    # Directory structure
    dirs = [
        target,
        target / "enums" / "_schema",
        target / "data",
        target / "engine",
        target / "logbook",
        target / "experiments",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Template file → output file mapping
    file_map = {
        "domain_config.py.template": f"engine/config.py",
        "convergence_runner.py.template": "experiments/convergence_runner.py",
        "audit_adapter.py.template": f"engine/audit.py",
        "enum_meta_schema.json.template": "enums/_schema/enum_meta_schema.json",
        "CLAUDE.md.template": "CLAUDE.md",
        "pre-commit.template": "hooks/pre-commit",
    }

    for template_name, output_rel in file_map.items():
        tmpl_path = TEMPLATES_DIR / template_name
        if not tmpl_path.exists():
            print(f"  SKIP: template not found: {template_name}")
            continue

        content = tmpl_path.read_text()
        # Replace ${VAR} placeholders
        for key, val in subs.items():
            content = content.replace(f"${{{key}}}", val)

        out_path = target / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        print(f"  {output_rel}")

    # Make pre-commit executable
    hook_path = target / "hooks" / "pre-commit"
    if hook_path.exists():
        hook_path.chmod(0o755)

    # Create minimal pyproject.toml
    pyproject = target / "pyproject.toml"
    pyproject.write_text(f"""[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "{slug}"
version = "0.1.0"
description = "{name} — Lazarus domain instance"
requires-python = ">=3.11"
dependencies = ["lazarus-protocol"]
""")
    print(f"  pyproject.toml")

    # Create engine/__init__.py
    (target / "engine" / "__init__.py").write_text("")
    (target / "experiments" / "__init__.py").write_text("")

    print(f"\nProject scaffolded at: {target}")
    print(f"\nNext steps:")
    print(f"  1. cd {target}")
    print(f"  2. Edit engine/config.py — set paths and thresholds")
    print(f"  3. Edit experiments/convergence_runner.py — add FACET_REGISTRY entries")
    print(f"  4. pip install -e . && pip install lazarus-protocol")
    print(f"  5. git init && git add -A && git commit -m 'Initial scaffold'")


def main():
    parser = argparse.ArgumentParser(
        prog="lazarus",
        description="Lazarus Protocol — Meta-Research Library CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="Scaffold a new domain project")
    p_init.add_argument("project_name", help="Project name (e.g. 'MyDomain')")
    p_init.add_argument("--path", help="Target directory (default: ./<project_name>)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        cmd_init(args)


if __name__ == "__main__":
    main()
