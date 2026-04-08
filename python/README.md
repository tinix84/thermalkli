# thermal-cli

Python port of the Octave thermal engineering library. See
[`docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md`](../docs/superpowers/specs/2026-04-08-octave-to-python-migration-design.md)
for the migration plan.

## Install (dev)

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest                    # all tests (requires octave installed for regression)
pytest tests/unit         # unit only (no octave needed)
pytest tests/regression   # regression only (needs octave)
```
