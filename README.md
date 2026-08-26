# Mapping as Code

**Versionable enterprise mapping contracts with deterministic validation, Excel/CSV import, semantic change analysis, lineage, and projections into adjacent enterprise-as-code tools.**

Enterprise mappings usually begin in Excel and then spread across tickets, migration workbooks, interface specifications, test evidence, and implementation code. That makes a simple question surprisingly difficult: **what exactly is mapped, why, what changed, is it complete, and what else depends on it?**

Mapping as Code turns mapping intent into a small, reviewable, machine-readable contract that can live in Git and participate in CI — without forcing transformation teams to abandon spreadsheets on day one.

## What works now

v0.3 can:

- import canonical mapping tables from CSV;
- import `.xlsx` / `.xlsm` workbooks with `Mappings` and optional `ValueMaps` sheets;
- load canonical YAML or JSON mapping specifications;
- validate structure and semantic mapping rules;
- detect duplicate mapping IDs and conflicting target assignments;
- validate lookup/value-map references;
- enforce required target-field coverage;
- flag unused required source fields;
- compare revisions by stable business mapping ID;
- produce field-level lineage as JSON or Mermaid;
- project the same mapping into **Transformation Graph**;
- generate a safe starting contract for **Reconciliation as Code**;
- project mapping lineage into **Enterprise Change Graph**;
- generate **Visual Workbench** Markdown/frontmatter for deterministic rendering;
- emit deterministic machine-readable output for CI and agents.

## Quick start

```bash
python -m pip install -e .
map-code validate examples/customer-master.yaml
```

```text
legacy-customer-to-s4-business-partner: 4 mappings, 100% required-target coverage
OK: no diagnostics
```

### Start from Excel or CSV

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

See [Importing existing mapping workbooks](docs/importing-workbooks.md).

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

The stable field mapping `id` is independent from source and target names. A rename is therefore a semantic change to the same rule, not an opaque delete/add pair.

## Semantic diff

```bash
map-code diff \
  examples/customer-master.yaml \
  examples/customer-master-v2.yaml
```

The diff distinguishes source, target, transform, rule, and business-metadata changes.

## Lineage

```bash
map-code lineage examples/customer-master.yaml --format mermaid
```

JSON output is available for machine use.

## One mapping, multiple enterprise views

### Transformation Graph

```bash
map-code project examples/customer-master.yaml \
  --target transformation-graph \
  -o mapping.transformation-graph.json
```

Systems, business objects, fields, and stable mapping rules become project graph nodes and edges.

### Reconciliation as Code

Runtime evidence locations and identity keys remain explicit rather than being guessed:

```bash
map-code project examples/customer-master.yaml \
  --target reconciliation-as-code \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  --format yaml \
  -o reconciliation.yaml
```

Only deterministic `copy` and `lookup` mappings automatically become field checks. Lookup dictionaries are preserved. Constants and arbitrary expressions are deliberately not converted into misleading equality checks.

### Enterprise Change Graph

```bash
map-code project examples/customer-master.yaml \
  --target enterprise-change-graph \
  -o mapping.change-graph.json
```

Projection preserves provenance and business criticality so mapping rules can participate in downstream impact analysis.

### Visual Workbench

```bash
map-code project examples/customer-master.yaml \
  --target visual-workbench \
  --format markdown \
  -o mapping-visual.md
```

The result is native Visual Workbench Markdown with three semantic lanes: source → mapping rules → target.

See [Interoperability](docs/interoperability.md) for the projection rules and safety boundaries.

## Why this is useful

### Migration and transformation projects

Keep field mappings reviewable, diffable, testable, and linked to required target coverage instead of treating the workbook as an opaque attachment.

### Integration design

Represent source-to-target intent separately from runtime middleware. Review the mapping before implementation and reuse it later for impact analysis and evidence generation.

### Data governance

Capture ownership, rationale, criticality, rules, and value maps close to the actual field relationship.

### Pull-request governance

A mapping change becomes a semantic diff instead of a line-level spreadsheet comparison.

### Agent context

Agents consume normalized contracts and projections rather than reverse-engineering workbooks repeatedly.

## CLI

```text
map-code import <csv|xlsx> [--value-maps values.csv] [-o mapping.yaml]
map-code validate <file> [--format text|json]
map-code diff <old> <new> [--format text|json]
map-code lineage <file> [--format json|mermaid]
map-code project <file> --target <target> [projection options]
```

Validation errors return exit code `1`; parse/import errors return exit code `2`.

## Specification and guides

- [v0.1 mapping semantics](docs/specification.md)
- [Workbook import convention](docs/importing-workbooks.md)
- [Cross-repository interoperability](docs/interoperability.md)
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
- provenance retained across projections;
- adjacent tools own execution, reconciliation, impact analysis, and presentation.

## Boundary

Mapping as Code is **not an ETL engine**. It defines and governs mapping intent. Execution runtimes and adjacent repositories consume its stable outputs.

## Related projects

- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph)
- [Visual Workbench](https://github.com/dkharlanau/visual-workbench)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph)

## Status

**Active — working v0.3.** The executable mapping core, spreadsheet bridge, and first cross-repository interoperability layer are implemented and exercised in CI. Next focus: governance evidence, breaking-change gates, and retained adapter conformance.
