# Interoperability

Mapping as Code owns mapping intent. v0.3 adds deterministic projections into adjacent repositories so one mapping contract can participate in transformation planning, reconciliation, impact analysis, and business visualization without duplicating source-of-truth logic.

## Transformation Graph

Target schema: `transformation-graph/schema/transformation-graph.schema.json`.

```bash
map-code project examples/customer-master.yaml \
  --target transformation-graph \
  --output mapping.transformation-graph.json
```

Projection rules:

- source/target systems become `system` nodes;
- source/target business objects become `business_object` nodes;
- fields become `field` nodes;
- the mapping set and each stable field mapping become `mapping` nodes;
- source fields connect to mapping rules with `input_to`;
- mapping rules connect to target fields with `maps_to`;
- transform/rule/business metadata remains attached to mapping nodes.

The output uses Transformation Graph v0.1 `version/project/nodes/edges` shape.

## Enterprise Change Graph

Target schema: `enterprise-change-graph/schema/enterprise-change-graph.schema.json`.

```bash
map-code project examples/customer-master.yaml \
  --target enterprise-change-graph \
  --output mapping.change-graph.json
```

The same mapping lineage becomes a change-impact graph with:

- explicit `provenance: mapping-as-code`;
- forward propagation edges;
- business criticality preserved on mapping nodes when present;
- mapping ID and schema version stored in graph metadata.

This makes mapping rules usable as impact-analysis seeds without making Mapping as Code responsible for the impact engine itself.

## Reconciliation as Code

Target schema: `reconciliation-as-code/schema/reconciliation.schema.json`.

Reconciliation needs runtime evidence endpoints and identity keys, so those remain explicit CLI inputs rather than being invented from mapping metadata.

```bash
map-code project examples/customer-master.yaml \
  --target reconciliation-as-code \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  --format yaml \
  --output reconciliation.yaml
```

Safety boundary:

- every projection gets a `record_coverage` check;
- `copy` mappings become `field_match` checks;
- `lookup` mappings become `field_match` checks with the declared value map;
- high/critical fields become critical materiality fields;
- constants and arbitrary expressions are **not** converted into equality checks because that would assert semantics the adapter cannot prove;
- composite keys are accepted as comma-separated values.

The generated reconciliation is a starting contract and can be enriched with scopes, tolerances, exceptions, or child collections in Reconciliation as Code.

## Visual Workbench

Target schema: `visual-workbench/schemas/visual-workbench.schema.json`.

Visual Workbench consumes Markdown + YAML frontmatter. Mapping as Code can emit that form directly:

```bash
map-code project examples/customer-master.yaml \
  --target visual-workbench \
  --format markdown \
  --output mapping-visual.md
```

The projection uses three semantic lanes:

1. source fields;
2. mapping rules;
3. target fields.

Each field mapping is a `step`, source/target fields are `data` nodes, and transforms appear on data edges. High-criticality mappings are marked with warning status; critical mappings use danger status. Presentation remains owned by Visual Workbench.

Then render it in Visual Workbench:

```bash
node dist/cli.js render mapping-visual.md -o mapping.svg
```

## Contract policy

Adapters are intentionally projections, not bidirectional synchronization. The canonical Mapping as Code document remains the source of truth.

Each adapter follows four rules:

1. deterministic output for deterministic input;
2. no access to SAP or another runtime required;
3. no inferred business semantics that cannot be proven from the mapping contract;
4. provenance retained so downstream graphs/evidence can trace back to the mapping source.

This allows the repositories to evolve independently while still behaving as one composable enterprise modeling toolkit.
