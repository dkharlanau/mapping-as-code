# Mapping as Code

**Turn enterprise mapping workbooks into governed, versionable contracts that can be reviewed, tested, compared, traced, and connected to the rest of a transformation architecture.**

Enterprise mappings usually begin in Excel and then fragment across tickets, migration workbooks, interface documents, test evidence, and implementation code. Mapping as Code keeps the mapping intent in one deterministic contract and derives the rest.

```text
CSV / Excel / YAML
        ↓
 Mapping as Code
        ├── validation + quality policy
        ├── semantic diff + PR gate
        ├── traceability + lineage
        ├── release / ecosystem evidence
        └── projections
             ├── Transformation Graph
             ├── Reconciliation as Code
             ├── Enterprise Change Graph
             ├── Visual Workbench
             └── Interface as Code binding
```

## v0.5 capabilities

- CSV, XLSX/XLSM, YAML, and JSON ingestion;
- stable field-mapping identities;
- deterministic validation and required-target coverage;
- sandboxed multi-file composition with namespaced reusable fragments;
- value-map, duplicate, and conflict diagnostics;
- semantic revision diff by `source`, `target`, `transform`, `rules`, and `business` metadata;
- transparent 0–100 quality score;
- reusable governance policy packs;
- breaking-change and quality-regression gates;
- GitHub annotations, compact PR summaries, file-level SARIF, and a reusable Action/workflow;
- Markdown/HTML catalogs and traceability matrices;
- deterministic repository catalog indexes, metadata search, and synthetic scale benchmarks;
- JSON, Mermaid, GraphML, and Cypher lineage;
- auditable release bundles with raw and canonical SHA-256;
- pinned-schema conformance tests for adjacent repositories;
- Mapping as Code → Interface as Code binding using the official `mapping.ref` contract;
- Mapping revision → Enterprise Change Graph transition seeds, including removed topology;
- one ecosystem evidence bundle containing all available cross-repository projections.

## Quick start

```bash
python -m pip install -e .
map-code validate examples/customer-master.yaml
map-code score examples/customer-master.yaml
```

Start from a workbook:

```bash
python -m pip install -e '.[excel]'
map-code import customer-mapping.xlsx -o mapping.yaml
map-code validate mapping.yaml
```

See [workbook import](docs/importing-workbooks.md).

## Canonical mapping contract

YAML and JSON contracts reject duplicate keys, including nested field definitions
and value maps. A repeated key must not silently replace a mapping or policy before
validation. Standard YAML anchor/merge defaults with an explicit override remain
supported. Invalid input returns CLI exit code `2` with the source path and a
diagnostic on stderr.

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

The stable field mapping `id` is independent from field names. A rename or transform change is therefore a semantic change to the same rule rather than an opaque delete/add pair.

## Governance

```bash
map-code report mapping.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o validation-report.json

map-code gate old.yaml new.yaml \
  --policy policies/enterprise-strict.yaml \
  -o breaking-report.json

map-code review old.yaml new.yaml \
  --policy policies/enterprise-strict.yaml \
  --format markdown \
  -o review.md
```

A policy can require ownership/rationale by criticality, set minimum quality, cap warnings, bound quality-score regression, and classify mapping changes as `ignore`, `info`, `warning`, or `error`.

Included packs:

- `policies/migration-pragmatic.yaml`
- `policies/enterprise-strict.yaml`

See [governance and evidence](docs/governance.md).

## GitHub PR governance

The repository ships a composite Action and reusable workflow.

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- uses: dkharlanau/mapping-as-code@main
  with:
    mapping-path: mappings/customer.yaml
    policy-path: mappings/policy.yaml
    baseline-ref: origin/main
```

The Action produces validation evidence, semantic review, Job Summary, workflow annotations, SARIF, and a release bundle. It fails when current governance or the semantic/quality transition gate fails.

For artifact upload and an idempotent PR comment, use the reusable workflow. See [GitHub integration](docs/github-action.md).

## Evidence

### Mapping-set discovery and scale checks

Build a deterministic index across a repository or directory, then search its mapping metadata:

```bash
map-code catalog-index mappings/ --output mapping-index.json --fail-on-duplicates
map-code catalog-search mappings/ "business partner" --output search-results.json
```

The index reports duplicate mapping IDs and skipped non-mapping documents without treating arbitrary YAML as a mapping. A synthetic benchmark exercises validation, lineage, and quality scoring without customer data:

```bash
map-code benchmark --fields 10000 --max-seconds 5 --output benchmark.json
```

Timing thresholds depend on the runner and are opt-in. See [catalog discovery and scale checks](docs/catalog-and-scale.md).

### Traceability and catalog

```bash
map-code traceability mapping.yaml -o traceability.json
map-code catalog mapping.yaml --format markdown -o catalog.md
map-code catalog mapping.yaml --format html -o catalog.html
```

### Release bundle

```bash
map-code bundle mapping.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o mapping-release.json
```

A release bundle retains:

```text
raw source SHA-256
canonical semantic SHA-256
policy-aware validation
traceability matrix
field-level lineage
```

### Ecosystem bundle

```bash
map-code ecosystem-bundle mapping-v2.yaml \
  --policy policies/migration-pragmatic.yaml \
  --baseline mapping-v1.yaml \
  --interface-file interface.yaml \
  --mapping-uri mappings/mapping-v2.yaml \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  -o ecosystem.json
```

Without runtime parameters the bundle contains only projections that can be derived safely. Reconciliation and Interface contracts are added only when their explicit inputs exist.

Each adjacent artifact carries its own canonical SHA and pinned target-contract metadata.

## Semantic diff and lineage

```bash
map-code diff old.yaml new.yaml
map-code lineage mapping.yaml --format mermaid -o lineage.mmd
map-code lineage mapping.yaml --format graphml -o lineage.graphml
map-code lineage mapping.yaml --format cypher -o lineage.cypher
```

GraphML and Cypher are deterministic exports of the same field-level lineage graph, not separate sources of truth.

## Adjacent enterprise-as-code contracts

### Transformation Graph

```bash
map-code project mapping.yaml \
  --target transformation-graph \
  -o mapping.transformation-graph.json
```

### Reconciliation as Code

Runtime evidence locations and identity keys remain explicit:

```bash
map-code project mapping.yaml \
  --target reconciliation-as-code \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  --mapping-artifact-file mapping.yaml \
  --mapping-artifact-sha256 <sha256> \
  --format yaml \
  -o reconciliation.yaml
```

Linked mode is the canonical source-of-truth integration: RAC lookup checks use `map_ref` and evidence pins the Mapping artifact. Omitting `--mapping-artifact-file` intentionally creates a detached snapshot with inline value maps for export/archive use. Only deterministic `copy` and `lookup` mappings automatically become field checks; arbitrary expressions are not converted into misleading equality checks. See [Mapping → Reconciliation integration](docs/reconciliation-integration.md).

### Enterprise Change Graph

Snapshot:

```bash
map-code project mapping.yaml --target enterprise-change-graph -o graph.json
```

Revision transition with impact seeds:

```bash
map-code change-graph mapping-v1.yaml mapping-v2.yaml -o transition.json
```

Removed rules remain in the transition topology and are marked `removed`, so impact traversal can still follow their previous dependencies.

### Visual Workbench

```bash
map-code project mapping.yaml \
  --target visual-workbench \
  --format markdown \
  -o mapping-visual.md
```

### Interface as Code

Mapping as Code does not invent interface trigger/delivery/retry/monitoring semantics. It binds an existing v1.0 interface contract to the exact mapping artifact:

```bash
map-code bind-interface interface.yaml mapping.yaml \
  --mapping-uri mappings/mapping.yaml \
  --revision main@abc123 \
  -o interface.bound.yaml
```

Endpoint mismatch fails by default. The generated `mapping.ref` uses the official Interface as Code artifact reference with canonical mapping SHA-256.

See [interoperability](docs/interoperability.md).

## Conformance

Target schemas are retained under `conformance/` with the upstream schema blob SHA and source URL. CI validates generated artifacts against those pinned contracts for:

- Transformation Graph v0.1;
- Reconciliation as Code v1;
- Enterprise Change Graph v1;
- Visual Workbench v1;
- Interface as Code v1.0.

This prevents cross-repository adapters from silently drifting as the ecosystem evolves.

## CLI

```text
map-code import <csv|xlsx> ...
map-code compose <manifest> [-o mapping.yaml]
map-code validate <file>
map-code score <file>
map-code report <file> [--policy ...]
map-code annotations <file> [--policy ...]
map-code sarif <file> [--policy ...] [-o results.sarif]
map-code diff <old> <new>
map-code gate <old> <new> [--policy ...]
map-code review <old> <new> [--max-items 20]
map-code lineage <file> [--format json|mermaid|graphml|cypher]
map-code traceability <file>
map-code catalog <file> [--format markdown|html]
map-code catalog-index <root> [--fail-on-duplicates]
map-code catalog-search <root> <query> [--limit 20]
map-code benchmark [--fields 10000] [--max-seconds N]
map-code bundle <file> [--policy ...]
map-code ecosystem-bundle <file> [cross-repository options]
map-code bind-interface <interface> <mapping> --mapping-uri ...
map-code change-graph <old> <new>
map-code project <file> --target <target> [projection options]
```

Governance failures return exit code `1`; parse/import/usage failures return `2`.

## Machine-readable contracts

- [Mapping schema](schema/mapping.schema.json)
- [Governance policy schema](schema/governance-policy.schema.json)
- [Validation report schema](schema/validation-report.schema.json)
- [Release bundle schema](schema/release-bundle.schema.json)
- [Ecosystem bundle schema](schema/ecosystem-bundle.schema.json)

## Guides

- [Documentation home](docs/index.md)
- [Mapping semantics](docs/specification.md)
- [Multi-file composition](docs/composition.md)
- [Catalog discovery and scale checks](docs/catalog-and-scale.md)
- [Workbook import](docs/importing-workbooks.md)
- [Governance and evidence](docs/governance.md)
- [GitHub Action/workflow](docs/github-action.md)
- [Cross-repository interoperability](docs/interoperability.md)
- [Roadmap](ROADMAP.md)

## Boundary

Mapping as Code is **not an ETL engine** and does not execute arbitrary expressions or infer missing runtime contracts. It defines and governs mapping intent. Execution, reconciliation, orchestration, impact analysis, and presentation remain owned by adjacent tools.

## Related projects

See [Mapping as Code in the as-code suite](docs/as-code-suite.md) for runnable handoffs and their limits.

- [Interface as Code](https://github.com/dkharlanau/interface-as-code) — bind the canonical mapping through the official `mapping.ref` without inventing interface operations.
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code) — reuse a pinned lookup mapping or generate a reviewed starting reconciliation contract.
- [Process as Code](https://github.com/dkharlanau/process-as-code) — reference mapping artifacts for process traceability without evaluating transformations.
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code) — keep bounded decisions distinct from field mappings and transformation expressions.

## Status

**Active — working v0.5.** Core, spreadsheet bridge, governance, PR-native review, pinned-schema interoperability, portable lineage exports, and cross-repository evidence are implemented and continuously tested.

## About the author

Created and maintained by **Dzmitryi Kharlanau**, an SAP consultant and system analyst working across enterprise architecture, data, integration, operations, and practical AI.

- [Website and knowledge base](https://dkharlanau.github.io/)
- [LinkedIn](https://www.linkedin.com/in/dkharlanau/)
