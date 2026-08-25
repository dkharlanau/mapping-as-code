# Mapping as Code

Versionable enterprise mapping specifications with validation, lineage, change analysis, and generated tests.

## Problem

Enterprise mappings are often scattered across Excel files, documents, emails, and project-specific templates. They are difficult to version, review, compare, validate, test, and trace.

## Core idea

Represent mappings as structured, versionable definitions instead of scattered spreadsheets and documents.

## Example

```yaml
source:
  system: legacy
  object: customer
  field: country

target:
  system: s4
  object: business-partner
  field: country

transform:
  type: lookup
  reference: country-map

rules:
  required: true
```

## Initial scope

- Excel/CSV mapping import
- canonical mapping model
- coverage validation
- conflicting mapping detection
- duplicate mapping detection
- missing target/source rules
- value-map validation
- version diff
- lineage visualization
- generated tests
- Markdown/HTML documentation

## Long-term direction

Become an open mapping specification format and compiler for enterprise transformation projects.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

## Related projects

- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph)

## Status

Planning.
