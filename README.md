# Mapping as Code

**Versionable enterprise mapping contracts with deterministic validation, change analysis, lineage, and an Excel/CSV bridge.**

Mapping documents usually begin in Excel and then spread across tickets, emails, migration workbooks, interface specifications, test evidence, and implementation code. That makes a simple question surprisingly difficult: **what exactly is mapped, why, what changed, and is the mapping complete?**

Mapping as Code turns that intent into a small, reviewable, machine-readable contract that can live in Git and participate in CI — while still accepting the spreadsheets transformation teams already use.

## What works now

v0.2 is an executable Python package and CLI. It can:

- import canonical mapping tables from CSV;
- import `.xlsx` / `.xlsm` workbooks with `Mappings` and optional `ValueMaps` sheets;
- load canonical YAML or JSON mapping specifications;
- validate mapping structure and semantic rules;
- detect duplicate mapping IDs and conflicting target assignments;
- validate lookup/value-map references;
- enforce required target-field coverage;
- flag unused required source fields;
- compare two mapping revisions by stable business mapping ID;
- produce field-level lineage as JSON or Mermaid;
- emit deterministic JSON suitable for CI, agents, and adjacent graph tools.

## Quick start

```bash
python -m pip install -e .
map-code validate examples/customer-master.yaml
```

Example output:

```text
legacy-customer-to-s4-business-partner: 4 mappings, 100% required-target coverage
OK: no diagnostics
```

### Start from an existing spreadsheet export

```bash
map-code import examples/customer-master.csv \
  --value-maps examples/customer-value-maps.csv \
  --output mapping.yaml

map-code validate mapping.yaml
```

For Excel:

```bash
python -m pip install -e '.[excel]'
map-code import customer-mapping.xlsx -o mapping.yaml
```

See [Importing existing mapping workbooks](docs/importing-workbooks.md) for the small interchange-table convention.

## A mapping contract

```yaml
schema_version: "0.1"

mapping:
  id: legacy-customer-to-s4-business-partner

  source:
    system: legacy-erp
    object: customer
    required_fields: [customer_id, country]

  target:
    system: s4hana
    object: business-partner
    required_fields: [BusinessPartner, Country]

  fields:
    - id: customer-id
      source:
        field: customer_id
      target:
        field: BusinessPartner
      transform:
        type: copy
      rules:
        required: true

    - id: customer-country
      source:
        field: country
      target:
        field: Country
      transform:
        type: lookup
        reference: iso-country

value_maps:
  iso-country:
    DE: DE
    US: US
```

The stable field mapping `id` matters: source/target names can change while the engine can still recognize that the same business mapping rule was modified.

## Why this is useful

### Migration and transformation projects

Keep field mappings reviewable, diffable, testable, and linked to required target coverage instead of treating the workbook as an opaque attachment.

### Integration design

Represent source-to-target intent separately from runtime middleware. A mapping can be reviewed before implementation and reused for impact analysis later.

### Data governance

Capture ownership, rationale, criticality, rules, and value maps close to the actual field relationship.

### Pull-request governance

A mapping change becomes a semantic diff: changed source, target, transformation, validation rule, or business meaning rather than a line-level spreadsheet comparison.

### Agent context

Agents can consume normalized JSON instead of reverse-engineering a workbook every time they need mapping context.

## CLI

```text
map-code import <csv|xlsx> [--value-maps values.csv] [-o mapping.yaml]
map-code validate <file> [--format text|json]
map-code diff <old> <new> [--format text|json]
map-code lineage <file> [--format json|mermaid]
```

Validation errors return exit code `1`, so mapping quality can be used directly as a CI gate.

## Specification

- [v0.1 mapping semantics](docs/specification.md)
- [Workbook import convention](docs/importing-workbooks.md)
- [JSON Schema](schema/mapping.schema.json)
- [Reference mapping](examples/customer-master.yaml)
- [Changed revision](examples/customer-master-v2.yaml)
- [CSV import example](examples/customer-master.csv)
- [Roadmap](ROADMAP.md)

## Design principles

- versionable and Git-friendly;
- deterministic before probabilistic;
- portable and vendor-neutral where practical;
- usable without access to SAP or another enterprise runtime;
- safe to inspect without executing arbitrary mapping expressions;
- business semantics and technical lineage in the same contract;
- machine-readable outputs first, visual views where useful;
- interoperable with transformation, reconciliation, change-impact, and visualization tooling.

## Boundary

Mapping as Code is **not an ETL engine**. It defines and governs mapping intent. Execution runtimes can consume the contract; other tools can use it for transformation planning, reconciliation, impact analysis, documentation, and visual explanation.

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
- [Visual Workbench](https://github.com/dkharlanau/visual-workbench)

## Status

**Active — working v0.2.** The executable core and spreadsheet bridge are implemented and covered by CI. The next loop focuses on governance evidence and stable cross-repository adapters.
