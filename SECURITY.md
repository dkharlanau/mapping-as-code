# Security policy

Mapping as Code processes structured mapping definitions, workbooks and generated artifacts. Treat those inputs as untrusted data. A mapping artifact is not executable authority merely because it is valid, versioned, linked from another repository or consumed by the GitHub Action.

## Supported versions

Security fixes target the current supported release line and `main`. When a vulnerability affects an older release, the advisory/release notes should state the earliest fixed version rather than implying indefinite support for every historical version.

## Reporting a vulnerability

Use GitHub's private vulnerability-reporting / Security Advisory workflow for this repository when available. Do not publish exploit details, credentials, proprietary mapping data or proof-of-concept payloads in a public issue.

A useful report includes:

- affected version or commit;
- input shape and command/action path involved;
- expected security boundary;
- observed behavior and impact;
- minimal privacy-safe reproduction steps.

Ordinary mapping mistakes, validation disagreements and feature requests can use public issues when they contain no sensitive data.

## Security boundaries

### Mapping input is data, not code

YAML/CSV/workbook mapping content may describe transformations and references, but consumers must not execute arbitrary embedded scripts or commands simply because a mapping is accepted. New executable/plugin mechanisms require an explicit trust model rather than being smuggled through a data field.

### File and composition boundaries

Import, composition and file-reference behavior is security-sensitive. Relative-path handling must remain bounded to the documented operation, and a crafted mapping should not gain arbitrary filesystem or network access through a path/reference field.

### Cross-repository use

A referenced or projected artifact remains untrusted input until the consumer validates the contract/version it explicitly supports. Hashes and versions establish identity/change detection; they do not establish authorization, business approval or positive assurance.

### GitHub Action permissions

The reusable Action runs with the permissions granted by the caller workflow. It must not require or silently widen repository/write permissions merely to validate a mapping. Users should grant the minimum permissions required by their surrounding workflow.

### Secrets and enterprise data

Credentials, tokens, passwords and private keys do not belong in portable mapping artifacts or public fixtures. Generated reports, bundles and evidence may contain source/target names, field metadata or values; review them before attaching them to public issues, Actions artifacts or releases.

Public repository examples should remain synthetic or deliberately non-sensitive.

## Examples of security issues

Security reports are appropriate for issues such as:

- path traversal or unintended arbitrary file access from crafted input;
- command/code execution from a mapping field that is documented as data-only;
- secret leakage into logs, reports or release artifacts;
- unsafe GitHub Action behavior that expands permissions or executes untrusted content;
- parser/resource behavior that enables practical denial of service outside documented limits;
- integrity/provenance bypass that can make different mapping content appear to be the pinned artifact.

A business-rule validation false positive/negative is normally a correctness defect unless it also crosses a security boundary.

## Security claim boundary

This project provides deterministic validation/governance controls; it does not claim formal security certification, sandboxing of arbitrary executable extensions, or suitability for handling confidential enterprise data without the user's surrounding access controls and review process.
