# Roadmap

## Shipped — v0.1 executable core

- [x] canonical YAML/JSON mapping model
- [x] published JSON Schema
- [x] stable field mapping identities
- [x] deterministic semantic validation
- [x] required target coverage
- [x] duplicate target and mapping-ID detection
- [x] value-map reference validation
- [x] semantic mapping diff
- [x] field-level lineage JSON
- [x] Mermaid lineage rendering
- [x] installable Python package and CLI
- [x] reference enterprise mapping revisions
- [x] unit tests and CI build gate

## Shipped — v0.2 spreadsheet bridge

- [x] CSV mapping workbook import
- [x] XLSX/XLSM mapping workbook import
- [x] `ValueMaps` sheet and companion CSV support
- [x] deterministic normalization of empty cells and booleans
- [x] generated canonical YAML/JSON
- [x] diagnostics for ambiguous/inconsistent workbook metadata
- [x] CI exercise of import → validate flow

## Shipped — v0.3 interoperability

- [x] Transformation Graph projection
- [x] Reconciliation as Code projection with explicit runtime endpoints
- [x] Enterprise Change Graph projection with provenance and propagation
- [x] Visual Workbench three-lane data-flow projection
- [x] Visual Workbench Markdown/frontmatter output
- [x] lookup maps projected into reconciliation field checks
- [x] criticality projected into materiality and visual status
- [x] projection contract tests and CI smoke tests

## P0 — governance and generated evidence

- [ ] configurable policy packs for critical fields, ownership, and rationale
- [ ] mapping quality scorecard
- [ ] generated Markdown/HTML mapping catalog
- [ ] traceability matrix
- [ ] machine-readable validation report schema
- [ ] breaking-change policy and CI gate
- [ ] release bundle with source hash and validation evidence

## P1 — deeper interoperability

- [ ] Interface as Code field-contract references
- [ ] change-diff seeds for Enterprise Change Graph
- [ ] adapter conformance reports against retained target-schema versions
- [ ] portable GraphML/Cypher export where useful
- [ ] generated cross-repository evidence bundle

## P1 — scale and enterprise ingestion

- [ ] multi-file mapping composition
- [ ] mapping namespaces and reusable fragments
- [ ] large mapping-set benchmarks
- [ ] mapping catalog search/index
- [ ] import profiles for common migration/integration workbook layouts
- [ ] optional agent-facing context bundles

## Product boundary

Mapping as Code governs mapping intent. It should remain deterministic, portable, and usable without access to SAP or another enterprise runtime. Execution, reconciliation, process orchestration, impact analysis, and visual presentation belong in adjacent tools and consume stable Mapping as Code outputs.
