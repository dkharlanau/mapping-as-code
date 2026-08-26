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

## Shipped — v0.4 governance and generated evidence

- [x] configurable policy packs for critical fields, ownership, and rationale
- [x] transparent mapping quality scorecard
- [x] generated Markdown/HTML mapping catalog
- [x] traceability matrix
- [x] machine-readable validation report schema
- [x] breaking-change policy and CI gate
- [x] release bundle with raw source hash, canonical hash, validation evidence, traceability, and lineage
- [x] governance policy JSON Schema
- [x] release bundle JSON Schema
- [x] schema conformance tests for policies and generated evidence

## Shipped — PR-native governance loop

- [x] reusable composite GitHub Action for validation + semantic gate
- [x] combined PR review report with quality delta and breaking events
- [x] retained baseline resolver from Git ref/path
- [x] Markdown Job Summary
- [x] reusable workflow with evidence artifact upload
- [x] idempotent PR comment update
- [x] self-dogfood Action CI using `uses: ./`

## Shipped — v0.5 review ergonomics and deeper interoperability

- [x] GitHub annotation commands for file-level diagnostics
- [x] file-level SARIF output without invented line numbers
- [x] compact executive PR summary for large mappings
- [x] configurable fail-on-quality-regression threshold
- [x] Interface as Code v1.0 artifact binding with endpoint safety
- [x] mapping-diff seeds and transition topology for Enterprise Change Graph
- [x] retained target schemas with pinned blob provenance
- [x] adapter conformance tests for Transformation Graph, Reconciliation, Change Graph, Visual Workbench, and Interface as Code
- [x] portable GraphML and Cypher lineage export
- [x] generated cross-repository ecosystem evidence bundle

## P0 — scale and enterprise ingestion

- [ ] multi-file mapping composition
- [ ] mapping namespaces and reusable fragments
- [ ] large mapping-set benchmarks
- [ ] mapping catalog search/index
- [ ] import profiles for common migration/integration workbook layouts
- [ ] optional agent-facing context bundles

## P1 — ecosystem hardening

- [ ] retained-contract drift checker against upstream schemas
- [ ] ecosystem bundle split/materialize command for downstream tools
- [ ] GraphML/Cypher transition-graph export
- [ ] release tags and immutable action examples
- [ ] compatibility matrix in generated documentation

## Product boundary

Mapping as Code governs mapping intent. It should remain deterministic, portable, and usable without access to SAP or another enterprise runtime. Execution, reconciliation, process orchestration, impact analysis, and visual presentation belong in adjacent tools and consume stable Mapping as Code outputs.
