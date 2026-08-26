# Agent instructions

Mapping as Code is a contract-first transformation tool. Treat mapping YAML as source material that must be validated, not as permission to infer missing business meaning.

## Working loop

1. Read `README.md`, the relevant mapping contract, and `docs/agent-manifest.json`.
2. Validate before generating or compiling anything: `python -m mac validate <mapping.yaml>`.
3. Use schema and coverage commands to inspect scope and gaps.
4. Compile only an explicitly requested supported target.
5. Preserve deterministic ordering and generated paths.
6. Return validation findings, generated artifacts, and evidence references separately.

## Guardrails

- Do not invent source fields, target fields, transforms, defaults, or business rules.
- Do not silently repair an invalid contract; report the issue and make any requested edit explicit.
- Keep generated files out of hand-authored source locations unless the repository already establishes that path.
- Prefer machine-readable CLI output where available.
- When interoperability is involved, verify the referenced Interface as Code or other upstream contract instead of copying its assumptions.

## Useful commands

```bash
python -m mac validate examples/order_mapping.yaml
python -m mac schema examples/order_mapping.yaml --direction target
python -m mac coverage examples/order_mapping.yaml
python -m mac compile examples/order_mapping.yaml --target python --out generated/order_mapping.py
python -m mac evidence-bundle examples/order_mapping.yaml
```
