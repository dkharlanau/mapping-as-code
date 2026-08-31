# Catalog discovery and scale checks

Mapping repositories become difficult to navigate when teams cannot answer three basic questions: which mapping contracts exist, whether stable mapping IDs collide, and where a relevant source, target, owner, or business object is defined.

## Build an index

```bash
map-code catalog-index mappings/ \
  --output mapping-index.json \
  --fail-on-duplicates
```

The command scans YAML, YML, and JSON files in deterministic path order. Files without a Mapping as Code `mapping` object are ignored. Files that cannot be parsed are listed under `skipped`; their content is not repaired or interpreted. Each mapping entry includes its stable ID, path, source and target identity, field count, required-target coverage, owners, criticalities, and canonical SHA-256.

`--fail-on-duplicates` returns exit code `1` when the same mapping ID appears in more than one document. Without the flag, duplicates remain visible evidence but do not fail the command.

## Search mapping metadata

```bash
map-code catalog-search mappings/ "business partner" \
  --limit 10 \
  --output search-results.json
```

Search is case-insensitive and requires every query token to occur in the indexed metadata. It searches IDs, titles, descriptions, paths, source and target systems/objects, owners, and criticalities. Results are ranked deterministically; this is metadata discovery, not semantic or vector search.

## Exercise a large mapping safely

```bash
map-code benchmark \
  --fields 10000 \
  --max-seconds 5 \
  --output benchmark.json
```

The benchmark creates an in-memory synthetic mapping and measures validation, lineage construction, and quality scoring. It never reads enterprise data. The output records each timing, diagnostic counts, lineage size, quality score, and whether the optional total-time threshold passed.

Timing is environment-dependent. Use `--max-seconds` only when the CI runner class is controlled; otherwise retain the result as comparative evidence rather than a universal performance claim.

## Practical CI gates

A conservative repository gate can combine:

```bash
map-code catalog-index mappings/ --fail-on-duplicates --output mapping-index.json
map-code benchmark --fields 10000 --output mapping-benchmark.json
```

Keep the generated evidence as a workflow artifact when it helps reviewers, but keep hand-authored mapping contracts as the source of truth.
