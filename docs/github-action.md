# GitHub governance integration

Mapping as Code ships both a composite Action and a reusable workflow.

## Composite Action

Use the Action when you want to control the surrounding workflow yourself.

```yaml
name: Mapping review

on:
  pull_request:
    paths:
      - mappings/**

jobs:
  mapping:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: dkharlanau/mapping-as-code@main
        id: mapping
        with:
          mapping-path: mappings/customer.yaml
          policy-path: mappings/policy.yaml
          baseline-ref: origin/main

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mapping-governance
          path: .mapping-as-code
```

The Action:

1. installs the Mapping as Code CLI from the Action checkout;
2. validates the current mapping under policy;
3. resolves a baseline from either `baseline-path` or `git show <baseline-ref>:<mapping-path>`;
4. generates one combined review report with quality delta and semantic change events;
5. writes a Markdown review into GitHub Job Summary;
6. produces an auditable release bundle;
7. fails the step if current governance or the semantic change gate fails.

`actions/checkout` should normally use `fetch-depth: 0` when `baseline-ref` is used.

## Action outputs

- `validation-report`
- `review-report`
- `summary`
- `release-bundle`

These are paths in the current workspace/output directory.

## Reusable workflow

For a smaller caller workflow:

```yaml
name: Mapping governance

on:
  pull_request:
    paths:
      - mappings/customer.yaml
      - mappings/policy.yaml

jobs:
  mapping:
    permissions:
      contents: read
      pull-requests: write
    uses: dkharlanau/mapping-as-code/.github/workflows/governance-reusable.yml@main
    with:
      mapping-path: mappings/customer.yaml
      policy-path: mappings/policy.yaml
      baseline-ref: origin/main
      comment-on-pr: true
```

The reusable workflow additionally:

- uploads `.mapping-as-code` as the `mapping-governance-evidence` artifact;
- creates or updates one PR comment identified by an internal marker instead of posting a new comment on every run.

## Baseline rules

### Git ref baseline

```yaml
baseline-ref: origin/main
```

The Action resolves:

```bash
git show origin/main:mappings/customer.yaml
```

This is useful for PR checks because it compares semantic mapping intent against the retained branch baseline rather than against line-level YAML changes.

### Local baseline

Use `baseline-path` when another workflow step has already prepared a baseline file.

If no baseline is supplied, the Action still validates the current mapping, generates a quality score, summary, and release bundle, but no semantic transition gate is run.

## Failure semantics

A PR review fails if either:

- the current mapping fails policy-aware validation/quality gates; or
- a semantic change event has severity `error` under the selected policy.

This means a mapping can be structurally valid but still fail because a target or transform changed in a breaking way.

## Security boundary

The Action does not execute mapping expressions or connect to enterprise systems. It reads repository files, evaluates deterministic governance rules, and emits derived evidence.
