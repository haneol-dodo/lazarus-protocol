# Lazarus Protocol

Meta-research library for probe-based exploration of unknown coordinate spaces.

## Cosmology

```
Tesseract (discovery) → Lazarus (collection) → Parallax (triangulation)
```

- **Tesseract**: domain-agnostic discovery framework (RPD + Satisficing)
- **Lazarus**: domain-agnostic collection protocol (C1-C11, probe/mission, convergence)
- **Parallax**: domain-specific instance (EFL coordinate system)

## Install

```bash
pip install -e .
```

Zero dependencies -- stdlib only, Python >= 3.11.

## Quick Start

```python
from lazarus.registry.domain import DomainRegistry

# Configure for your domain
registry = DomainRegistry(
    name="my-domain",
    project_root="/path/to/project",
    schema_dir="/path/to/project/enums",
    data_dir="/path/to/project/data",
    meta_schema_path="/path/to/project/enums/_schema/meta.json",
)

# Audit
report = registry.audit_full()
print(report.summary())

# Categorical convergence
cc = registry.build_categorical_convergence()
data = cc.init_axis_data("facet.name", ["high", "medium", "low"])
cc.add_run(data, "claude_h1", "claude", 1, {"entity1": "high", "entity2": "low"})
analysis = cc.analyze_axis(data)

```

## Bootstrap a New Domain

Copy and customize files from `templates/`:

```
templates/
  domain_config.py.template      # DomainRegistry setup
  convergence_runner.py.template  # CLI for convergence runs
  audit_adapter.py.template       # Thin adapter over lazarus.audit
  enum_meta_schema.json.template  # Minimal meta-schema
  CLAUDE.md.template              # Lazarus-compliant CLAUDE.md
  pre-commit.template             # Git pre-commit hook
```

Replace `${DOMAIN_NAME}`, `${domain_name}`, etc. with your project values.

## Core Modules

| Module | Purpose |
|--------|---------|
| `lazarus.data.sextuple` | Sextuple + FacetDefinition dataclasses |
| `lazarus.data.io` | JSON/CSV I/O utilities |
| `lazarus.audit.core` | Violation, AuditReport, BaseAuditor |
| `lazarus.audit.checks` | Pure constraint check functions (C1-C9) |
| `lazarus.audit.schema_auditor` | Auditor 1: enum schema integrity |
| `lazarus.audit.boundary_auditor` | Auditor 2: calculator boundary enforcement |
| `lazarus.convergence.categorical` | Categorical (enum) convergence engine |
| `lazarus.convergence.display` | CLI display functions |
| `lazarus.convergence.types` | Result dataclasses |
| `lazarus.registry.domain` | DomainRegistry central config |
| `lazarus.prompt.template` | LLM estimation prompt templates |
| `lazarus.hooks.pre_commit` | Pre-commit hook generator |

## Protocol

See `CLAUDE.md` for the full Lazarus Protocol v3.0.0 specification.

## Tests

```bash
python -m pytest tests/
```
