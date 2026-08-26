# Mapping as Code

**Versionable enterprise mapping contracts with workbook import, deterministic validation, policy gates, evidence bundles, lineage, and projections into adjacent enterprise-as-code tools.**

Enterprise mappings usually begin in Excel and then spread across tickets, migration workbooks, interface specifications, test evidence, and implementation code. That makes basic questions difficult: **what exactly is mapped, why, who owns it, what changed, is it complete, and is the change safe to release?**

Mapping as Code turns mapping intent into a small, reviewable, machine-readable contract that can live in Git and participate in CI — without forcing transformation teams to abandon spreadsheets on day one.

## What works now

v0.4 can:

- import mapping tables from CSV, `.xlsx`, and `.xlsm`;
- load canonical YAML/JSON specifications;
- validate structure, required target coverage, duplicate mappings, and value-map references;
- compare revisions by stable mapping IDs;
- generate field-level lineage and traceability;
- calculate a transparent 0–100 mapping quality score;
- apply reusable governance policy packs for ownership, criticality, rationale, warning limits, and quality thresholds;
- classify source/target/transform/rule/business changes and block breaking revisions in CI;
- generate machine-readable validation reports with canonical SHA-256;
- generate Markdown and standalone HTML mapping catalogs;
- build auditable release bundles containing raw source hash, canonical hash, validation evidence, traceability, and lineage;
- project the same mapping into **Transformation Graph**, **Reconciliation as Code**, **Enterprise Change Graph**, and **Visual Workbench**.

## Quick start

```bash
python -m pip install -e .
map-code validate examples/customer-master.yaml
map-code score examples/customer-master.yaml
```

Start from an existing workbook:

```bash
python -m pip install -e '.[excel]'
map-code import customer-mapping.xlsx -o mapping.yaml
map-code validate mapping.yaml
```

See [Importing existing mapping workbooks](docs/importing-workbooks.md).

## Governance

Use a reusable policy pack:

```bash
map-code report examples/customer-master.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o validation-report.json
```

A policy can require field ownership and rationale by criticality, set a minimum quality score, cap warnings, and classify semantic changes as `ignore`, `info`, `warning`, or `error`.

Two reference packs are included:

- `policies/migration-pragmatic.yaml` — practical migration governance;
- `policies/enterprise-strict.yaml` — stronger stewardship and release controls.

### Breaking-change gate

```bash
map-code gate \
  examples/customer-master.yaml \
  examples/customer-master-v2.yaml \
  --policy policies/enterprise-strict.yaml \
  -o breaking-report.json
```

Exit code `1` means the revision violates policy. By default, removing a stable mapping or changing its target/transform is breaking; source/rule/business changes remain reviewable and policy-configurable.

See [Governance and evidence](docs/governance.md).

## Quality score

```bash
map-code score examples/customer-master.yaml --format json
```

The score is intentionally explainable, not heuristic. Its 100 points are split across:

- structural/semantic validity — 35;
- required target coverage — 25;
- ownership — 15;
- rationale — 10;
- criticality metadata — 10;
- stable mapping IDs — 5.

The detailed dimension values are emitted with the score.

## Generated evidence

### Traceability matrix

```bash
map-code traceability examples/customer-master.yaml -o traceability.json
```

Each row retains the stable mapping ID, qualified source and target field, transform, value-map reference, required flag, owner, criticality, and rationale.

### Mapping catalog

```bash
map-code catalog examples/customer-master.yaml \
  --format markdown \
  -o mapping-catalog.md

map-code catalog examples/customer-master.yaml \
  --format html \
  -o mapping-catalog.html
```

The HTML catalog is standalone and contains no runtime dependency.

### Release bundle

```bash
map-code bundle examples/customer-master.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o mapping-release.json
```

The bundle contains:

```text
source file SHA-256
        +
canonical document SHA-256
        +
policy-aware validation report
        +
traceability matrix
        +
field-level lineage
```

This allows a retained artifact to prove what source was reviewed and which normalized mapping contract was validated.

## A mapping contract

```yaml
schema_version: "0.1"

mapping:
  id: legacy-customer-to-s4-business-partner
  title: Legacy customer to S/4HANA Business Partner

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
      source: {field: customer_id}
      target: {field: BusinessPartner}
      transform: {type: copy}
      rules: {required: true}
      business:
        owner: master-data
        criticality: high
        rationale: Stable cross-system business identity.

    - id: customer-country
      source: {field: country}
      target: {field: Country}
      transform:
        type: lookup
        reference: iso-country

value_maps:
  iso-country:
    DE: DE
    US: US
```

The stable field mapping `id` is independent from source and target names. A rename is therefore a semantic change to the same rule, not an opaque delete/add pair.

## Semantic diff and lineage

```bash
map-code diff examples/customer-master.yaml examples/customer-master-v2.yaml
map-code lineage examples/customer-master.yaml --format mermaid
```

Diff distinguishes `source`, `target`, `transform`, `rules`, and `business` changes. Lineage is available as JSON or Mermaid.

## One mapping, multiple enterprise views

### Transformation Graph

```bash
map-code project examples/customer-master.yaml \
  --target transformation-graph \
  -o mapping.transformation-graph.json
```

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

Only deterministic `copy` and `lookup` mappings automatically become field checks. Constants and arbitrary expressions are deliberately not converted into misleading equality checks.

### Enterprise Change Graph

```bash
map-code project examples/customer-master.yaml \
  --target enterprise-change-graph \
  -o mapping.change-graph.json
```

### Visual Workbench

```bash
map-code project examples/customer-master.yaml \
  --target visual-workbench \
  --format markdown \
  -o mapping-visual.md
```

See [Interoperability](docs/interoperability.md) for projection rules and safety boundaries.

## CLI

```text
map-code import <csv|xlsx> [--value-maps values.csv] [-o mapping.yaml]
map-code validate <file> [--format text|json]
map-code score <file> [--format text|json]
map-code report <file> [--policy policy.yaml] [-o report.json]
map-code diff <old> <new> [--format text|json]
map-code gate <old> <new> [--policy policy.yaml] [-o report.json]
map-code lineage <file> [--format json|mermaid]
map-code traceability <file> [-o traceability.json]
map-code catalog <file> [--format markdown|html] [-o catalog]
map-code bundle <file> [--policy policy.yaml] [-o bundle.json]
map-code project <file> --target <target> [projection options]
```

Validation/governance failures return exit code `1`; parsing/import/usage failures return exit code `2`.

## Machine-readable contracts

- [Mapping schema](schema/mapping.schema.json)
- [Governance policy schema](schema/governance-policy.schema.json)
- [Validation report schema](schema/validation-report.schema.json)
- [Release bundle schema](schema/release-bundle.schema.json)

Schemas and generated contracts are exercised in CI.

## Guides

- [Mapping semantics](docs/specification.md)
- [Workbook import convention](docs/importing-workbooks.md)
- [Governance and evidence](docs/governance.md)
- [Cross-repository interoperability](docs/interoperability.md)
- [Roadmap](ROADMAP.md)

## Design principles

- versionable and Git-friendly;
- deterministic before probabilistic;
- portable and vendor-neutral where practical;
- usable without SAP/runtime access;
- no execution of arbitrary mapping expressions during governance;
- business semantics and technical lineage in the same contract;
- policy and scoring must remain explainable;
- retained provenance across generated evidence and projections;
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

**Active — working v0.4.** Executable mapping core, spreadsheet bridge, cross-repository interoperability, governance policy packs, breaking-change gates, generated catalogs, traceability, and release evidence are implemented and continuously tested.
