# Mapping as Code

**Versionable enterprise mapping specifications with validation, semantic diffs, spreadsheet import, and generated documentation.**

Enterprise mapping logic still lives surprisingly often in Excel files, email threads, workshop notes, middleware screenshots, and migration workbooks. That makes mappings hard to review, compare, validate, test, reuse, and trace.

Mapping as Code puts the mapping contract in Git.

```yaml
- id: country
  source: {path: KNA1.LAND1}
  target: {path: Country}
  transform:
    type: lookup
    reference: country-code
  constraints:
    required: true
```

## What works now

The repository contains a runnable Python MVP rather than only a format proposal:

- canonical YAML/JSON mapping format and JSON Schema;
- structural + semantic validation;
- duplicate and target-collision detection;
- value-map validation;
- semantic mapping diff keyed by stable field IDs;
- CSV import and optional XLSX import;
- Markdown documentation generation;
- SAP customer → S/4HANA Business Partner example;
- automated tests and GitHub Actions CI.

## Quickstart

```bash
python -m pip install -e '.[dev]'
mapcode validate examples/sap-customer.yaml
mapcode diff examples/sap-customer.yaml examples/sap-customer-v2.yaml
mapcode docs examples/sap-customer.yaml -o mapping.md
```

Import an existing mapping table:

```bash
mapcode import examples/import-template.csv \
  --name legacy-customer \
  --source-system LEGACY_ERP \
  --source-object CUSTOMER \
  --target-system S4HANA \
  --target-object BUSINESS_PARTNER \
  -o mapping.yaml
```

See [Quickstart](docs/quickstart.md) and the [v1alpha1 specification](docs/specification.md).

## Why not just keep the Excel?

Excel is useful as an editing surface. It is weak as the source of truth for transformation logic. A canonical mapping specification enables deterministic checks before a migration load or interface deployment and makes pull-request review meaningful.

The project therefore treats spreadsheets as **inputs/outputs**, not as the canonical contract.

## CLI

| Command | Purpose |
|---|---|
| `mapcode validate FILE...` | Validate structure and mapping semantics |
| `mapcode diff BEFORE AFTER` | Show added, removed, and changed mapping IDs |
| `mapcode docs FILE` | Generate human-readable Markdown |
| `mapcode import FILE.csv` | Convert a mapping table into canonical YAML |

XLSX import is supported with `pip install -e '.[excel]'`.

## Validation examples

The validator can already catch common project defects before runtime: duplicate mapping IDs, duplicate source → target rows, target collisions, missing value maps, duplicate value-map keys, and incomplete transforms.

## SAP proving ground

The format is vendor-neutral, but SAP migration, MDG, and integration work are deliberate proving grounds. The included example uses familiar customer master fields such as `KNA1.KUNNR`, `KNA1.NAME1`, and `KNA1.LAND1` mapped to S/4HANA Business Partner targets.

See [SAP-oriented use cases](docs/sap-use-cases.md).

## Direction

Next: richer workbook adapters, coverage rules, generated mapping tests, lineage graphs, machine-readable impact reports, and interoperability adapters.

The boundary is deliberate: **Mapping as Code is a specification/compiler layer, not another ETL runtime.**

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

**Core MVP implemented. Format: `v1alpha1`.**

MIT License.
