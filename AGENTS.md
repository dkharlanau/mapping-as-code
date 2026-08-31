# Agent instructions

Mapping as Code is a contract-first transformation tool. Treat mapping YAML as source material that must be validated, not as permission to infer missing business meaning.

## Working loop

1. Read `README.md`, the relevant mapping contract, and `docs/agent-manifest.json`.
2. Validate before generating anything: `map-code validate <mapping.yaml>`.
3. Use score, traceability, catalog, and lineage commands to inspect scope and gaps.
4. Generate only an explicitly requested supported report, bundle, or projection.
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
map-code validate examples/customer-master.yaml
map-code score examples/customer-master.yaml --format json
map-code traceability examples/customer-master.yaml --output traceability.json
map-code lineage examples/customer-master.yaml --format mermaid --output lineage.mmd
map-code bundle examples/customer-master.yaml --output release-bundle.json
```
