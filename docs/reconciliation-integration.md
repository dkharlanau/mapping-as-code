# Mapping → Reconciliation integration

Mapping as Code owns transformation intent. Reconciliation as Code owns the evidence that source and target state satisfy explicit controls. The same lookup rule should not be maintained independently in both products.

## Canonical mode: linked source

Use a RAC-relative Mapping artifact path and, for governed/release use, pin its SHA-256. The generated reconciliation keeps copy checks directly and represents lookup checks with RAC `map_ref`. RAC resolves the original Mapping as Code field at runtime and records the exact artifact digest in evidence.

```bash
map-code project mapping.yaml \
  --target reconciliation-as-code \
  --source-file legacy.csv \
  --target-file s4.csv \
  --source-key customer_id \
  --target-key BusinessPartner \
  --mapping-artifact-file mapping.yaml \
  --mapping-artifact-sha256 <64-hex-sha256> \
  --format yaml \
  -o reconciliation.yaml
```

The path is interpreted by RAC relative to the reconciliation specification, so generate/copy artifacts into a stable layout rather than relying on a workstation-specific absolute path.

The generated contract declares `generated_from.projection_mode: linked_source`. This is the preferred mode when Mapping as Code remains the maintained transformation source of truth.

## Detached mode: snapshot

If `--mapping-artifact-file` is omitted, Mapping as Code embeds compatible lookup tables into the generated RAC spec. The contract declares `generated_from.projection_mode: detached_snapshot`.

Use this only when a self-contained point-in-time artifact is intentionally required, for example an archive, handoff bundle or isolated fixture. Editing the detached map later creates an independent source of truth and is therefore not the normal portfolio architecture.

## Boundaries

- Mapping as Code does not decide whether migrated data passed reconciliation.
- Reconciliation as Code does not become the authoring system for transformation rules merely because it can consume them.
- Only Mapping as Code `lookup` transforms are imported through `map_ref` today. Unsupported/ambiguous transforms fail or remain outside generated equality checks rather than being guessed.
- Mapping artifact SHA changes alter RAC configuration provenance; a stale SHA pin fails closed.

This rule keeps the cross-repository chain directional: **author transformation once → reference it → produce reconciliation evidence**.
