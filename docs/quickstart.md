# Quickstart

Mapping as Code keeps transformation logic in Git as structured specifications that machines can validate and people can review.

## Install

```bash
python -m pip install -e .
```

For Excel import:

```bash
python -m pip install -e '.[excel]'
```

## Validate

```bash
mapcode validate examples/sap-customer.yaml
```

A non-zero exit code means the specification contains schema or semantic errors, so the same command can gate pull requests.

## Compare mapping versions

```bash
mapcode diff examples/sap-customer.yaml examples/sap-customer-v2.yaml
```

The diff is keyed by stable field IDs rather than YAML line numbers.

## Generate documentation

```bash
mapcode docs examples/sap-customer.yaml -o mapping.md
```

## Import an existing spreadsheet-like mapping

CSV columns: `id, source, target, transform, reference, required, description`.

```bash
mapcode import examples/import-template.csv \
  --name legacy-customer \
  --source-system LEGACY_ERP \
  --source-object CUSTOMER \
  --target-system S4HANA \
  --target-object BUSINESS_PARTNER \
  -o mapping.yaml
```

XLSX uses the same header names and is available through the optional `excel` dependency.
