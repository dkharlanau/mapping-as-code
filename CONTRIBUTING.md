# Contributing

The project is intentionally small and deterministic-first. Changes should make mapping intent easier to version, validate, review, or exchange.

## Local checks

```bash
python -m pip install -e '.[dev]'
pytest -q
mapcode validate examples/sap-customer.yaml examples/sap-customer-v2.yaml
```

## Design rules

- Keep the canonical format vendor-neutral where practical.
- Prefer explicit deterministic transforms over hidden runtime behavior.
- Treat stable mapping IDs as public identifiers once published.
- Add a failing test before changing validation semantics.
- Avoid turning the core package into an ETL execution engine.
- New format features must be documented in `docs/specification.md`.
