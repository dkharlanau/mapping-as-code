# SAP Customer → Business Partner mapping preflight

This synthetic starter demonstrates a practical migration-mapping workflow from an ordinary Excel workbook into governed Mapping as Code artifacts and an optional Reconciliation as Code handoff.

It is designed for the practitioner job behind searches such as **SAP customer to business partner field mapping**, **SAP S/4HANA mapping workbook validation**, and **SAP migration mapping review**.

## Files

- [`customer-bp-mapping.xlsx`](customer-bp-mapping.xlsx) — downloadable synthetic mapping workbook with `Mappings` and `ValueMaps` sheets.
- [`legacy-customers.csv`](legacy-customers.csv) — synthetic legacy customer extract.
- [`s4-business-partners.csv`](s4-business-partners.csv) — synthetic S/4 Business Partner extract retaining `LegacyCustomerID` for explicit reconciliation identity.

No customer/client data or copied SAP product content is included.

## 1. Run the workbook preflight

Install the Excel extra and run:

```bash
pip install -e '.[excel]'

map-code-preflight \
  examples/sap-s4hana/customer-bp-mapping/customer-bp-mapping.xlsx \
  --policy policies/migration-pragmatic.yaml \
  --source-file examples/sap-s4hana/customer-bp-mapping/legacy-customers.csv \
  --target-file examples/sap-s4hana/customer-bp-mapping/s4-business-partners.csv \
  --source-key KUNNR \
  --target-key LegacyCustomerID \
  --output-dir build/sap-customer-bp-mapping
```

Expected artifacts:

```text
build/sap-customer-bp-mapping/
  mapping.yaml
  validation-report.json
  quality-score.json
  preflight-summary.json
  reconciliation.yaml
```

`mapping.yaml` is the canonical imported Mapping as Code contract. The validation and quality reports are derived evidence. `reconciliation.yaml` is generated only when the mapping is valid and all four RAC handoff arguments were supplied explicitly.

## 2. What the workbook deliberately models

The starter contains these mapping patterns:

| Legacy field | S/4 target | Mapping type | Why |
| --- | --- | --- | --- |
| `KUNNR` | `BusinessPartner` | expression / explicit identity resolution | Customer and BP technical IDs are not assumed equal. |
| `NAME1` | `OrganizationName1` | copy | Direct semantic field mapping. |
| `LAND1` | `Country` | lookup | Uses the explicit `country-code` value map. |
| `KTOKD` | `BusinessPartnerGrouping` | lookup | Uses an explicit synthetic account-group → BP-grouping map. |
| `VKORG` | `SalesOrganization` | copy | Demonstrates optional sales-area context. |
| `STCD1` | `TaxNumber` | copy | Demonstrates a business-critical field with no invented formatting rule. |

The identity mapping is intentionally **not** reduced to a source/target equality check. Mapping as Code records the explicit transformation intent; the generated RAC handoff skips unsupported arbitrary-expression equality checks and uses `KUNNR` → `LegacyCustomerID` as the explicit reconciliation identity supplied on the command line.

## 3. Review a changed workbook

For a real project, retain the canonical mapping from the previous reviewed revision and compare the next imported workbook against it:

```bash
map-code-preflight next-revision.xlsx \
  --baseline build/sap-customer-bp-mapping/mapping.yaml \
  --output-dir build/sap-customer-bp-mapping-next
```

The preflight adds `semantic-review.json` and `semantic-review.md`. It still does not authorize the change; it makes the semantic delta reviewable.

## Boundaries

This starter does **not** claim to be the canonical SAP Customer → BP mapping for every landscape. Real projects differ by CVI design, account groups/groupings, partner roles, tax handling, address model, sales areas, extensions and migration approach.

The tool therefore does not:

- infer business mappings from similar field names;
- invent account-group or country conversions;
- invent crosswalks, tolerances or expected counts;
- execute data migration;
- certify SAP readiness or migration correctness.

Use the workbook as a governed starting pattern, then replace the synthetic mapping intent with reviewed project-specific rules. Use Reconciliation as Code separately to prove the resulting source/target business state.