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

When later review must point back to workbook rows, write a separate provenance sidecar:

```bash
map-code import examples/customer-master.csv \
  --value-maps examples/customer-value-maps.csv \
  --output mapping.yaml \
  --provenance-output import-provenance.json
```

The sidecar records file, sheet, and physical row locations when available. It is not part of the canonical mapping contract, so moving a workbook row does not change the mapping semantic hash.

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

The importer treats the workbook reader as a trust boundary. It rejects input before dictionary construction or normalization can silently discard information.

For CSV and Excel inputs it rejects duplicate headers after whitespace normalization and internal blank headers. CSV rows must have the same number of cells as the header. Diagnostics retain the physical CSV row where a record starts, including records that contain multiline quoted values. Excel diagnostics retain the workbook path, sheet, row, and column when available.

Value-map keys are unique within a named map. Conflicting definitions are errors that report both source locations. Exact duplicate definitions are also rejected instead of being silently collapsed.

Excel formulas are never executed. When a mapping/value-map cell contains a formula, import uses only a cached value saved by the spreadsheet application. If no cached value exists, import fails and asks for the workbook to be recalculated and saved first. XLSM macros are not executed.

The importer also fails deterministically when workbook metadata is ambiguous. For example, one file cannot silently contain two different values for `target_system` or `mapping_id`. It rejects rows without a target field, non-constant rows without a source field, and constants without a value.

Text values remain text, including identifiers with leading zeros. Authors should therefore store identifiers that require leading zeros as text in the workbook instead of relying on display-only number formatting.

The importer performs conservative normalization only. The generated contract should then pass through `map-code validate`, which applies semantic mapping rules such as lookup reference integrity, duplicate target detection, and required-target coverage.

## Why metadata is repeated per row

Many enterprise mapping workbooks rely on merged cells, worksheet names, colors, comments, or convention-specific header blocks. Those are difficult to parse reliably and make automation fragile.

The v0.2 import format instead defines a deterministic interchange table. Existing customer-specific workbook layouts can later be supported through import profiles that map their columns into this canonical table.
