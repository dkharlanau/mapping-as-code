# Governance and evidence

Mapping as Code treats governance as deterministic evaluation of mapping intent, not as a workflow engine.

## Governance pipeline

```text
mapping source
    ↓
canonical mapping contract
    ↓
structural + semantic validation
    ↓
policy requirements
    ↓
quality score
    ↓
change classification / breaking gate
    ↓
validation report + release evidence
```

The same contract drives human catalogs, CI gates, lineage, and downstream projections.

## Policy packs

A policy pack is YAML or JSON matching `schema/governance-policy.schema.json`.

```yaml
version: 1
name: enterprise-strict

requirements:
  title_required: true
  criticality_required: true
  owner_required_for: [medium, high, critical]
  rationale_required_for: [high, critical]

quality:
  minimum_score: 85
  max_warnings: 3

breaking_changes:
  removed: error
  source: warning
  target: error
  transform: error
  rules: warning
  business: warning
  value_map: error
```

Policies deliberately use a small vocabulary. A rule should be explainable to a consultant or architect without knowing the implementation.

## Quality score

The score is a deterministic 100-point scorecard:

| Dimension | Maximum |
| --- | ---: |
| Structural and semantic validity | 35 |
| Required target coverage | 25 |
| Ownership metadata | 15 |
| Rationale metadata | 10 |
| Criticality metadata | 10 |
| Stable mapping IDs | 5 |

Every dimension is emitted separately. The score is not an AI confidence score and should not be treated as one.

## Policy-aware validation report

```bash
map-code report mapping.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o validation-report.json
```

The report contains:

- mapping ID;
- canonical SHA-256;
- policy name/version;
- mapping summary and required-target coverage;
- quality score and dimension breakdown;
- structural and policy diagnostics;
- explicit gate results;
- final `valid` status.

The contract is published in `schema/validation-report.schema.json`.

## Breaking changes

`map-code gate` compares stable field mapping IDs and classifies semantic changes.

```bash
map-code gate old.yaml new.yaml \
  --policy policies/enterprise-strict.yaml \
  -o breaking-report.json
```

The policy can independently classify:

- removed mapping;
- source change;
- target change;
- transform change;
- rule change;
- business metadata change;
- value-map entry or map removal/change.

Added value maps and added value-map entries are reported as information. Existing value-map entries use the configured `value_map` severity because changing a lookup result can change downstream behavior without changing the field rule itself.

Allowed severities are `ignore`, `info`, `warning`, and `error`. Any `error` event blocks the gate.

The default policy treats removal, target changes, and transform changes as breaking because they can change downstream behavior while retaining the same stable mapping identity.

## Functional review

`map-code review` adds a consultant-focused view on top of the raw change events.

```bash
map-code review old.yaml new.yaml \
  --policy policies/enterprise-strict.yaml \
  --format markdown \
  -o review.md
```

For every affected field, the review shows the stable rule ID, source, target, transform, required-target status, owner, criticality, rationale, and the reason a decision is required. A change to a referenced value map also marks the lookup rule for review even when the field mapping itself did not change.

Workbook source locations stay outside the canonical mapping so row movement does not change the semantic hash. Import can write a separate provenance sidecar:

```bash
map-code import next.xlsx \
  --output next.yaml \
  --provenance-output next-provenance.json

map-code review old.yaml next.yaml \
  --old-provenance old-provenance.json \
  --new-provenance next-provenance.json \
  --format markdown
```

The preflight command writes `import-provenance.json` automatically and uses it in the current revision review. Use `--baseline-provenance` when the retained baseline has a sidecar.

## Traceability

```bash
map-code traceability mapping.yaml -o traceability.json
```

Each row contains:

- stable mapping ID;
- fully-qualified source field;
- fully-qualified target field;
- transform type;
- lookup reference;
- required flag;
- owner;
- criticality;
- rationale.

This is a compact machine-facing matrix and is also reused by generated catalogs and release bundles.

## Mapping catalog

```bash
map-code catalog mapping.yaml --format markdown -o catalog.md
map-code catalog mapping.yaml --format html -o catalog.html
```

The catalog is derived output. It must never become the authoritative mapping source.

The standalone HTML renderer intentionally uses no JavaScript or remote assets so generated evidence remains portable.

## Release bundle

```bash
map-code bundle mapping.yaml \
  --policy policies/migration-pragmatic.yaml \
  -o release-bundle.json
```

A bundle records both the source-file hash and canonical-document hash:

```text
source.sha256       proves the exact reviewed file bytes
canonical_sha256    proves the normalized mapping semantics
```

It then embeds the policy-aware validation report, traceability matrix, and lineage graph.

The contract is published in `schema/release-bundle.schema.json`.

## CI pattern

A pull request can use two complementary gates:

```bash
map-code report new.yaml --policy policies/enterprise-strict.yaml
map-code gate old.yaml new.yaml --policy policies/enterprise-strict.yaml
```

The first asks whether the new contract itself is acceptable. The second asks whether the transition from the retained baseline is safe under change policy.

This separation is intentional: a mapping can be individually valid while still containing a breaking change.

## Boundary

Governance does not execute transformation expressions, query SAP, reconcile runtime data, or infer business approval. It evaluates only the declared mapping contract and deterministic policy rules.
