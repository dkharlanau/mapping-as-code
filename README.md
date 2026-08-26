# Mapping as Code

**Versionable enterprise mapping contracts with deterministic validation, change analysis, and lineage.**

Mapping documents usually begin in Excel and then spread across tickets, emails, migration workbooks, interface specifications, test evidence, and implementation code. That makes a simple question surprisingly difficult: **what exactly is mapped, why, what changed, and is the mapping complete?**

Mapping as Code turns that intent into a small, reviewable, machine-readable contract that can live in Git and participate in CI.

## What works now

v0.1 is an executable Python package and CLI. It can:

- load YAML or JSON mapping specifications;
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

Compare revisions:

```bash
map-code diff \
  examples/customer-master.yaml \
  examples/customer-master-v2.yaml
```

Generate lineage:

```bash
map-code lineage examples/customer-master.yaml --format mermaid
```

Machine-facing output is available with `--format json`.

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

Agents can consume the normalized JSON output instead of reverse-engineering an Excel workbook every time they need mapping context.

## CLI

```text
map-code validate <file> [--format text|json]
map-code diff <old> <new> [--format text|json]
map-code lineage <file> [--format json|mermaid]
```

Validation errors return exit code `1`, so mapping quality can be used directly as a CI gate.

## Specification

- [v0.1 semantics](docs/specification.md)
- [JSON Schema](schema/mapping.schema.json)
- [Reference mapping](examples/customer-master.yaml)
- [Changed revision](examples/customer-master-v2.yaml)
- [Roadmap](ROADMAP.md)

## Design principles

- versionable and Git-friendly;
- deterministic before probabilistic;
- portable and vendor-neutral where practical;
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

**Active — working v0.1 core.** Validation, semantic diff, lineage, examples, tests, packaging, and CI are implemented. The next product loop focuses on spreadsheet ingestion, generated mapping documentation, policy packs, and cross-repository contracts.
