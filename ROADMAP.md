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

## P0 — spreadsheet bridge

The fastest path from existing project artifacts into Mapping as Code.

- [ ] CSV mapping workbook import
- [ ] XLSX mapping workbook import
- [ ] value-map sheet/import support
- [ ] deterministic normalization of empty cells and booleans
- [ ] generated canonical YAML
- [ ] import diagnostics for ambiguous/inconsistent workbook metadata

## P1 — governance and generated evidence

- [ ] configurable policy packs for critical fields, ownership, and rationale
- [ ] mapping quality scorecard
- [ ] generated Markdown/HTML mapping catalog
- [ ] traceability matrix
- [ ] machine-readable validation report schema
- [ ] breaking-change policy and CI gate
- [ ] release bundle with source hash and validation evidence

## P1 — interoperability

- [ ] Transformation Graph adapter
- [ ] Reconciliation as Code projection
- [ ] Enterprise Change Graph impact seed format
- [ ] Visual Workbench semantic view export
- [ ] Interface as Code field-contract references
- [ ] portable GraphML/Cypher export where useful

## P2 — scale and enterprise ingestion

- [ ] multi-file mapping composition
- [ ] mapping namespaces and reusable fragments
- [ ] large mapping-set benchmarks
- [ ] mapping catalog search/index
- [ ] import profiles for common migration/integration workbook layouts
- [ ] optional agent-facing context bundles

## Product boundary

Mapping as Code governs mapping intent. It should remain deterministic, portable, and usable without access to SAP or another enterprise runtime. Execution, reconciliation, process orchestration, and visual presentation belong in adjacent tools and consume stable Mapping as Code outputs.
