# Roadmap

## v0.1 — Core MVP

- [x] canonical `MappingSpec` format
- [x] JSON Schema
- [x] semantic validator
- [x] stable-ID semantic diff
- [x] CSV import
- [x] optional XLSX import
- [x] Markdown documentation generator
- [x] SAP customer mapping example
- [x] tests and CI

## v0.2 — Project-workbook ingestion

- [ ] configurable column aliases instead of one fixed spreadsheet header
- [ ] multi-sheet XLSX import
- [ ] value-map sheet detection
- [ ] import diagnostics with row/column references
- [ ] canonical normalization command

## v0.3 — Mapping quality

- [ ] coverage rules against source/target field catalogs
- [ ] unmapped mandatory-target detection
- [ ] data-type compatibility checks
- [ ] unused value-map detection
- [ ] policy profiles for migration vs integration projects

## v0.4 — Generated evidence

- [ ] mapping-derived test cases
- [ ] Markdown + HTML reports
- [ ] Mermaid/DOT lineage graphs
- [ ] JSON impact report for pull requests and agents
- [ ] mapping-change risk scoring

## v0.5 — Interoperability

- [ ] pluggable import/export adapters
- [ ] SAP-oriented workbook templates and Migration Cockpit research spike
- [ ] interface payload mapping adapter
- [ ] reconciliation link format
- [ ] transformation-graph export

## Non-goal

Do not build a general-purpose ETL runtime. Keep the core focused on mapping specification, validation, change analysis, evidence, and exchange.
