# Mapping specification v1alpha1

The format describes field-level enterprise transformations independently of a specific ETL, SAP, cloud, or integration product.

## Document shape

A mapping has six useful concepts:

1. `metadata` — identity, version, owners, and tags.
2. `source` — source system, business object, and optional key fields.
3. `target` — target system, business object, and optional key fields.
4. `fields` — deterministic field-level mappings with stable IDs.
5. `transform` — how a source value becomes a target value.
6. `valueMaps` — reusable deterministic lookup tables.

The JSON Schema in `schemas/mapping.schema.json` is the normative structural definition for the current alpha format.

## Field identity

Every field mapping has a stable `id`. The ID is the unit used by semantic diffing and should survive harmless reordering.

## Supported transforms

- `copy` — source value is copied as-is.
- `lookup` — source value is translated through a named `valueMap`.
- `constant` — target receives a fixed value.
- `concat` — reserved for deterministic concatenation semantics.
- `expression` — escape hatch for implementations that need an explicit expression language.

## Semantic validation

In addition to JSON Schema validation, the CLI detects duplicate field IDs, duplicate source-to-target mappings, target collisions, missing lookup references, duplicate value-map keys, missing sources, and constants without values.

## Versioning rule

The current API version is `mappingascode.dev/v1alpha1`. Breaking format changes should introduce a new API version rather than silently changing existing semantics.
