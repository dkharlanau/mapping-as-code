# Mapping as Code in the as-code suite

Mapping as Code owns field-level transformation intent. The suite integrations remain directional: an interface may reference the mapping, and reconciliation may reuse or derive checks from it, but neither downstream artifact becomes a second mapping source of truth.

## Bind a mapping to an interface

The `bind-interface` command validates endpoint compatibility and writes the official Interface as Code `mapping.ref` shape:

```bash
map-code bind-interface \
  examples/customer-interface.yaml \
  examples/customer-master.yaml \
  --mapping-uri mappings/customer-master.yaml \
  --revision main@COMMIT_SHA \
  --output /tmp/customer-interface.bound.yaml
```

Only the mapping artifact reference and a missing profile are updated. Trigger, delivery, retry, monitoring, ownership, and reconciliation semantics remain owned by Interface as Code. Endpoint mismatch fails unless an operator explicitly accepts the exception.

## Produce a reconciliation starting contract

Mapping as Code can project compatible mapping rules into Reconciliation as Code v1:

```bash
mkdir -p /tmp/mapping-rac-handoff
cp examples/customer-master.yaml \
  /tmp/mapping-rac-handoff/customer-master.yaml

map-code project examples/customer-master.yaml \
  --target reconciliation-as-code \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  --mapping-artifact-file customer-master.yaml \
  --format yaml \
  --output /tmp/mapping-rac-handoff/reconciliation.yaml
```

The linked-source mode keeps compatible lookup rules as `map_ref` references. Copy rules become field checks and high/critical fields can become materiality inputs. Constants and arbitrary expressions are not converted into equality checks because the projection cannot prove their runtime semantics. The result is a starting control that must still be reviewed and run in Reconciliation as Code.

## Related projects

- [Interface as Code](https://github.com/dkharlanau/interface-as-code) has a tested `mapping.ref` contract. Mapping as Code can bind to it without inventing operational interface behavior.
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code) can consume pinned lookup mappings directly or run a reviewed projected contract.
- [Process as Code](https://github.com/dkharlanau/process-as-code) can resolve mapping artifacts through generic process traceability; it does not evaluate mapping semantics.
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code) governs bounded decisions. Keep decision logic separate unless a mapping transform is truly representable by the Mapping as Code transform model.

## Handoff rule

Pin immutable revisions and canonical hashes for governed handoffs. A successful projection proves schema compatibility, not that target data is correct or that an interface is production-ready.
