# Mapping as Code documentation

Mapping as Code turns source-to-target mapping intent into a deterministic contract that can be validated, reviewed, compared, traced, and projected into supported adjacent contracts. It does not move data or execute arbitrary transformation expressions.

## Start here

- [Specification](specification.md) — canonical mapping structure and semantics.
- [Workbook import](importing-workbooks.md) — deterministic CSV and Excel ingestion.
- [Multi-file composition](composition.md) — sandboxed reusable fragments and namespaces.
- [Governance and evidence](governance.md) — policies, quality scoring, gates, and release bundles.
- [GitHub Action](github-action.md) — PR-native governance and evidence retention.

## Operate mapping sets

- [Catalog discovery and scale checks](catalog-and-scale.md) — repository indexes, search, duplicate-ID gates, and synthetic benchmarks.
- [Interoperability](interoperability.md) — supported projections and pinned conformance contracts.
- [Reconciliation integration](reconciliation-integration.md) — linked and detached Reconciliation as Code projections.
- [Composition](composition.md) — deterministic provenance for multi-file mapping sources.

## Release and project boundaries

- [Release discipline](releases.md) — immutable tags, package verification, and optional PyPI publication.
- [Roadmap](../ROADMAP.md) — shipped capabilities and remaining work.
- [Security policy](../SECURITY.md) — input, file, Action, and data-handling boundaries.

For a runnable introduction, return to the [repository README](../README.md#quick-start).
