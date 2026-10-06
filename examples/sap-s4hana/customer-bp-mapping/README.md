# SAP Customer → Business Partner mapping review

This synthetic starter shows a controlled migration-mapping lifecycle from a workbook to a reviewed Mapping as Code contract and a Reconciliation as Code handoff.

The example is designed around a practical review question:

> What changed in the mapping, where did it come from, and should this revision be allowed to continue?

No customer data, client mapping, or copied SAP product content is included.

## Files

Baseline:

- [`customer-bp-mapping.xlsx`](customer-bp-mapping.xlsx) — synthetic baseline workbook with `Mappings` and `ValueMaps` sheets.
- [`legacy-customers.csv`](legacy-customers.csv) — baseline source extract.
- [`s4-business-partners.csv`](s4-business-partners.csv) — baseline target extract with `LegacyCustomerID`.

Review fixtures:

- [`customer-bp-mapping-malformed.csv`](customer-bp-mapping-malformed.csv) — duplicate header; import must fail before a canonical mapping is written.
- [`customer-bp-mapping-v2-broken.csv`](customer-bp-mapping-v2-broken.csv) — valid table structure with deliberate mapping and governance problems.
- [`customer-bp-value-maps-v2-broken.csv`](customer-bp-value-maps-v2-broken.csv) — deliberate change to the `DE` country conversion.
- [`customer-bp-mapping-v2-corrected.csv`](customer-bp-mapping-v2-corrected.csv) — corrected revision with one reviewed additive field.
- [`customer-bp-value-maps-v2-corrected.csv`](customer-bp-value-maps-v2-corrected.csv) — original mappings plus an additive `FR` entry.
- [`legacy-customers-v2.csv`](legacy-customers-v2.csv) and [`s4-business-partners-v2.csv`](s4-business-partners-v2.csv) — synthetic evidence for the corrected handoff.

## 1. Create the approved baseline

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

The baseline produces:

```text
mapping.yaml
validation-report.json
quality-score.json
import-provenance.json
preflight-summary.json
reconciliation.yaml
```

`mapping.yaml` contains the mapping semantics. `import-provenance.json` contains file, sheet, and row locations. Keeping them separate means a row move does not change the canonical mapping hash.

## 2. Protect the intake boundary

The malformed fixture contains a duplicate `target_field` header:

```bash
map-code-preflight \
  examples/sap-s4hana/customer-bp-mapping/customer-bp-mapping-malformed.csv \
  --output-dir build/sap-customer-bp-malformed
```

Expected result: exit code `2`.

No `mapping.yaml` should be created. The problem exists before semantic mapping review, so the input is rejected instead of being repaired or guessed.

This separates two different failure classes:

- **input failure** — the workbook cannot be read without losing evidence;
- **mapping review failure** — the input is readable, but the declared mapping change is not acceptable.

## 3. Review a deliberately broken revision

Run the structured but problematic revision against the retained baseline:

```bash
map-code-preflight \
  examples/sap-s4hana/customer-bp-mapping/customer-bp-mapping-v2-broken.csv \
  --value-maps examples/sap-s4hana/customer-bp-mapping/customer-bp-value-maps-v2-broken.csv \
  --policy policies/migration-pragmatic.yaml \
  --baseline build/sap-customer-bp-mapping/mapping.yaml \
  --baseline-provenance build/sap-customer-bp-mapping/import-provenance.json \
  --output-dir build/sap-customer-bp-broken
```

Expected result: exit code `1`.

The revision is readable, so Mapping as Code creates review evidence. The review should show several independent problems:

| Stable rule | Deliberate change | Review reason |
| --- | --- | --- |
| `name` | `copy` → expression | Transformation intent changed. |
| `country` | target `Country` → `CountryCode` | Target contract changed. |
| `country` | owner removed | High-criticality mapping lost required ownership. |
| `country-code` | `DE: DE` → `DE: D` | Referenced lookup behavior changed. |

The `country` finding also points to its physical source row. A value-map change is not hidden just because the field mapping still references the same map name.

This revision must not produce an approved handoff.

## 4. Correct the revision

The corrected revision restores the reviewed behavior and adds one explicit field:

`ORT01 → CityName`

It also adds `FR → FR` to the country value map without changing existing lookup results.

```bash
map-code-preflight \
  examples/sap-s4hana/customer-bp-mapping/customer-bp-mapping-v2-corrected.csv \
  --value-maps examples/sap-s4hana/customer-bp-mapping/customer-bp-value-maps-v2-corrected.csv \
  --policy policies/migration-pragmatic.yaml \
  --baseline build/sap-customer-bp-mapping/mapping.yaml \
  --baseline-provenance build/sap-customer-bp-mapping/import-provenance.json \
  --source-file examples/sap-s4hana/customer-bp-mapping/legacy-customers-v2.csv \
  --target-file examples/sap-s4hana/customer-bp-mapping/s4-business-partners-v2.csv \
  --source-key KUNNR \
  --target-key LegacyCustomerID \
  --output-dir build/sap-customer-bp-corrected
```

Expected result: exit code `0`.

The functional review shows `city` as an added rule. The existing `country` rule is also visible because its referenced value map changed, but the additive `FR` entry is informational under the pragmatic policy.

The generated Reconciliation as Code handoff includes a `city` field check. It still excludes the `legacy-id` expression because an arbitrary identity expression must not be reduced to a false equality check.

## 5. Mapping patterns in the baseline

| Legacy field | S/4 target | Mapping type | Purpose |
| --- | --- | --- | --- |
| `KUNNR` | `BusinessPartner` | expression | Explicit identity-resolution intent. |
| `NAME1` | `OrganizationName1` | copy | Direct field mapping. |
| `LAND1` | `Country` | lookup | Explicit governed country map. |
| `KTOKD` | `BusinessPartnerGrouping` | lookup | Synthetic account-group to BP-grouping map. |
| `VKORG` | `SalesOrganization` | copy | Sales-area context without invented conversion. |
| `STCD1` | `TaxNumber` | copy | Critical field without invented formatting logic. |

Technical customer and BP IDs are not assumed equal. The reconciliation identity is supplied explicitly as `KUNNR → LegacyCustomerID`.

## SAP Lead assessment explanation

A useful way to explain the design is:

> The workbook is not trusted only because Excel can open it. First, I protect the intake boundary so duplicate columns or conflicting lookup values cannot disappear silently. Then I compare stable mapping IDs and value maps with the approved revision. The review shows the business owner, field intent, source row, and the exact semantic change. Only a valid reviewed mapping can produce the reconciliation handoff. Mapping as Code owns transformation intent; Reconciliation as Code owns runtime evidence.

This separates four concerns:

1. **Input integrity** — can the workbook be read without losing information?
2. **Mapping governance** — is the declared transformation complete and owned?
3. **Change control** — what changed against the approved revision?
4. **Runtime proof** — does the resulting source/target state reconcile?

## Boundaries

This starter is not a universal Customer → Business Partner mapping. Real landscapes differ in CVI design, account groups, groupings, partner roles, tax handling, address data, sales areas, extensions, and migration approach.

The tool does not:

- infer mappings from similar field names;
- invent country or account-group conversions;
- invent identity crosswalks or tolerances;
- execute migration;
- connect to production SAP;
- treat a quality score as business approval.

Use the synthetic example as a review pattern, then replace its mapping intent with project-specific rules that have been reviewed by the responsible functional and data owners.
