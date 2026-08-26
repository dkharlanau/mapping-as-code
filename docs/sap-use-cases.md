# SAP-oriented use cases

Mapping as Code is vendor-neutral, but SAP transformation projects are a primary proving ground because they often combine business mapping, technical mapping, value mapping, and cutover evidence in spreadsheets.

## S/4HANA migration

A field mapping can represent a legacy customer field such as `KNA1.LAND1` and its target Business Partner field. A named lookup can capture country normalization. Git then gives the mapping a review history that is usually missing from project spreadsheets.

## MDG and replication

The format can document which source attributes populate MDG or downstream S/4 fields and make conflicting target ownership visible before runtime replication.

## Integration mapping

The same model can express payload-to-payload mappings for IDoc, API, event, or file interfaces. It does not attempt to replace CPI, PI/PO, middleware, or transformation runtimes; it provides a portable specification and validation layer around mapping intent.

## Cutover

Teams can freeze a mapping version for a rehearsal, compare it with the next version, and generate reviewable documentation. A mapping commit can then be referenced from reconciliation evidence or cutover tasks.

## Boundary

This project should not become a generic ETL runtime. The core value is specification, validation, change control, evidence, and interoperability.
