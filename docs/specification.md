# Mapping as Code v0.1

Mapping as Code treats an enterprise mapping as an executable contract rather than a spreadsheet attachment.

## Document model

A document contains:

- `schema_version` — format compatibility boundary.
- `mapping.id` — stable identity for the mapping set.
- `mapping.source` and `mapping.target` — system/object endpoints and optional required-field contracts.
- `mapping.fields` — stable field mappings with source, target, transform, rules, and business context.
- `value_maps` — named lookup dictionaries referenced by field transforms.

The canonical JSON Schema is in [`schema/mapping.schema.json`](../schema/mapping.schema.json).

## Stable field identity

Each field mapping has an `id`. The ID is deliberately separate from source and target field names so that a rename can be recognized as a change to the same business rule instead of a delete/add pair.

## Transform types

v0.1 recognizes `copy`, `lookup`, `constant`, `expression`, `concat`, `split`, `date`, `number`, and `boolean`.

The engine validates transform metadata but does not execute arbitrary expressions. This keeps validation deterministic and safe while allowing implementation-specific expression syntax to be documented.

## Validation semantics

`map-code validate` currently enforces:

1. mapping identity and source/target object identity;
2. non-empty field mapping set;
3. unique field mapping IDs;
4. target fields mapped at most once unless `allow_multiple_sources: true` is explicit;
5. defined lookup references;
6. values on constant mappings;
7. complete coverage of `target.required_fields`;
8. warnings for unused `source.required_fields`.

Errors produce exit code `1`, allowing the validator to act as a CI gate. Parse or I/O failures produce exit code `2`.

## Change analysis

`map-code diff old.yaml new.yaml` compares field mappings by stable ID. It distinguishes:

- added mappings;
- removed mappings;
- changes to source;
- changes to target;
- changes to transform logic;
- changes to validation rules;
- changes to business metadata.

The JSON output is intended for pull-request checks and downstream change graphs.

## Lineage

`map-code lineage` produces a portable field-level graph. JSON is the machine-facing representation; Mermaid is the human-facing representation.

A constant is represented as its own source node, so every target field still has an explicit lineage edge.

## Design boundary

Mapping as Code owns mapping intent and mapping governance. It does not try to become an ETL runtime. Execution engines can consume the contract, while adjacent tools can use its deterministic outputs for transformation planning, reconciliation, impact analysis, and visual explanation.
