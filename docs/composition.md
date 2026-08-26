# Multi-file mapping composition

Large enterprise mappings are easier to own when reusable or domain-specific rules can live in separate files. Mapping as Code composition keeps that modularity without introducing arbitrary file inclusion or a second execution model.

## Model

Composition has three artifacts:

```text
base mapping.yaml
      +
country.fragment.yaml
      +
address.fragment.yaml
      ↓
composition manifest
      ↓
canonical Mapping as Code document
```

The output is an ordinary Mapping as Code contract. After composition, every normal command works unchanged: `validate`, `report`, `gate`, `bundle`, `project`, and so on.

## Manifest

```yaml
composition_version: 1
base: customer-base.yaml
fragments:
  - path: country.fragment.yaml
    namespace: geo
  - path: address.fragment.yaml
    namespace: address
```

```bash
map-code compose customer.composition.yaml \
  -o customer.yaml \
  --report-output composition-report.json
```

The report records SHA-256 for the manifest, base, and each fragment plus the canonical hash of the final mapping.

## Fragment

A fragment deliberately contains only mapping-level reusable material:

```yaml
fragment_version: 1
fields:
  - id: country
    source: {field: country}
    target: {field: Country}
    transform:
      type: lookup
      reference: iso-country

value_maps:
  iso-country:
    DE: DE
    USA: US

required_fields:
  source: [country]
  target: [Country]
```

A fragment cannot redefine the mapping identity, source system/object, target system/object, title, or other base-contract metadata.

## Namespaces

A fragment namespace prevents stable-ID and local value-map collisions.

With `namespace: geo`:

```text
field id      country       → geo:country
local map     iso-country   → geo:iso-country
lookup ref    iso-country   → geo:iso-country
```

Only lookup references to maps declared inside that fragment are rewritten. A reference to a value map already provided by the base mapping remains unchanged.

This allows a fragment to depend deliberately on a shared/global map without silently cloning it.

## Required fields

Fragment `required_fields.source` and `required_fields.target` are merged into the base endpoint requirements while preserving order and uniqueness.

The composed contract must still satisfy ordinary coverage validation. A fragment cannot mark a target field required without also providing a valid mapping for it somewhere in the final contract.

## Safety boundary

All referenced files must be relative to the manifest directory.

Rejected:

```text
/etc/mapping.yaml
../outside.yaml
symlink -> outside composition directory
```

Paths are resolved before use and must remain inside the manifest directory. This keeps composition local, portable, and safe for CI/agent use.

## Collision rules

Composition fails when:

- two final field mappings have the same stable ID;
- two value maps end with the same name but different content;
- a fragment has an invalid namespace;
- a fragment or base path escapes the composition root;
- the final composed document fails normal Mapping as Code validation.

Identical value maps with the same final name are allowed because they do not introduce semantic ambiguity.

## Schemas

- `schema/composition-manifest.schema.json`
- `schema/mapping-fragment.schema.json`

The fragment schema is self-contained. Example manifests/fragments and the composed result are validated in CI.

## Design rule

Fragments are a source-organization mechanism, not a new semantic layer. The canonical composed mapping remains the artifact used for review, governance, evidence, and downstream projections.
