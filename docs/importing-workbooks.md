# Importing existing mapping workbooks

Mapping as Code is intended to meet transformation teams where they already work: CSV and Excel.

## CSV

Use one row per field mapping. Required workbook metadata is repeated on each row so the file remains portable and understandable without hidden workbook state.

Required columns:

- `mapping_id`
- `source_system`
- `source_object`
- `target_system`
- `target_object`
- `target_field`

Common optional columns:

- `id` — stable field mapping identity; generated from source/target when omitted
- `source_field` — required except for a `constant` transform
- `transform` — defaults to `copy`
- `reference` — named value map for `lookup`
- `value` — constant value for `constant`
- `expression` — documented expression for `expression`
- `required_source`
- `required_target`
- `owner`
- `criticality`
- `rationale`
- `allow_multiple_sources`

Boolean values accept `true`, `yes`, `y`, `1`, `x`, or `required`.

Import the reference example:

```bash
map-code import examples/customer-master.csv \
  --value-maps examples/customer-value-maps.csv \
  --output mapping.yaml

map-code validate mapping.yaml
```

A separate CSV value-map file uses three columns:

```text
map,source,target
iso-country,DE,DE
iso-country,US,US
```

## Excel

Install the optional Excel dependency:

```bash
python -m pip install -e '.[excel]'
```

The workbook convention is deliberately small:

- sheet `Mappings` — same columns as the CSV format;
- sheet `ValueMaps` — optional `map`, `source`, `target` columns.

If a `Mappings` sheet does not exist, the active sheet is treated as the mapping sheet.

```bash
map-code import customer-mapping.xlsx -o customer-mapping.yaml
map-code validate customer-mapping.yaml
```

`.xlsx` and `.xlsm` files are supported. Macros are not executed.

## Import diagnostics

The importer fails deterministically when workbook metadata is ambiguous. For example, one file cannot silently contain two different values for `target_system` or `mapping_id`.

It also rejects rows without a target field, non-constant rows without a source field, and constants without a value.

The importer performs normalization only. The generated contract should then pass through `map-code validate`, which applies semantic mapping rules such as lookup reference integrity, duplicate target detection, and required-target coverage.

## Why metadata is repeated per row

Many enterprise mapping workbooks rely on merged cells, worksheet names, colors, comments, or convention-specific header blocks. Those are difficult to parse reliably and make automation fragile.

The v0.2 import format instead defines a deterministic interchange table. Existing customer-specific workbook layouts can later be supported through import profiles that map their columns into this canonical table.
