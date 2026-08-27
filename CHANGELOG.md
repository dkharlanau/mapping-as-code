# Changelog

All notable public changes are recorded here. Mapping as Code uses semantic package versions and keeps mapping contract/schema evolution explicit in release notes.

## 0.5.0 — release candidate

This release establishes Mapping as Code as a governed mapping-contract toolkit rather than a YAML-only prototype.

### Mapping contract and authoring
- Canonical versioned mapping specification with JSON Schema and conformance fixtures.
- CSV/workbook import and value-map ingestion for migration-shaped mapping inventories.
- Sandboxed multi-file composition with reusable/namespaced fragments and deterministic collision handling.
- Stable field IDs so reviews and semantic diffs survive label/documentation changes.

### Review and governance
- Structural/semantic validation, quality scoring and policy profiles.
- Stable-ID semantic diff, breaking-change gates and combined PR review output.
- SARIF governance evidence and reusable GitHub Action support.
- Auditable release/evidence bundles with deterministic mapping identity.

### Navigation and interoperability
- Lineage export to Mermaid, GraphML and Cypher.
- Mapping catalogs/search and traceability output.
- Interface as Code binding plus projections for Transformation Graph, Enterprise Change Graph, Reconciliation as Code and Visual Workbench.
- Ecosystem evidence bundle joining mapping validation/review with related portfolio artifacts.

### Product surface
- Human-first GitHub Pages product page and repository agent capability manifest.
- CI across Python 3.10 and 3.12 covering representative imports, composition, governance, projections and Action execution.

### Boundaries
- Mapping as Code describes and governs mapping intent; it does not connect to production SAP systems or execute enterprise writes.
- Generated projections are interoperability artifacts, not a replacement for the target product's own validation/evidence contract.
- Runtime/package distribution is separate from the mapping specification version and remains subject to release compatibility policy.
