# Release discipline

Mapping as Code separates normal development CI from public package publication.

## Version authority

The Python package version in `pyproject.toml` is the release version. A public release tag must be exactly `v<package-version>`; for the current package this is `v0.5.0`.

Mapping specification/schema compatibility is documented separately from package implementation changes. A package release must not silently redefine an already published contract version.

## Release gate

The release workflow rebuilds artifacts from the tagged repository state and verifies:

1. tag and package version match;
2. source distribution and wheel build successfully;
3. package metadata passes `twine check`;
4. the built wheel installs into a clean virtual environment;
5. the installed `map-code` CLI starts and validates the reference mapping;
6. the exact verified `dist/` artifacts are retained for the release job.

Pull requests that change release metadata run the same verification without publishing.

## GitHub Release

A valid `v*` tag creates a GitHub Release from the verified sdist/wheel artifacts and generated GitHub release notes. If artifact verification fails, no release job runs.

Do not recreate an existing version with different bytes. If a public release artifact is wrong, fix forward with a new package version and document the defect.

## PyPI

PyPI publication is intentionally opt-in. It requires:

- a PyPI Trusted Publisher configured for this repository, workflow and `pypi` environment;
- repository variable `PYPI_PUBLISH_ENABLED=true`.

No long-lived PyPI token is part of the repository contract. When the variable is absent/false, a GitHub Release can still be produced without attempting PyPI publication.

## Failed publication

A failed PyPI upload does not change or rewrite the already verified GitHub artifacts. Diagnose the Trusted Publisher/environment problem, then retry the same immutable tag only when PyPI confirms that the version was not partially published. If package bytes need to change, increment the package version first.

## Release checklist

- Main CI green.
- `CHANGELOG.md` reviewed for the target version.
- `pyproject.toml` version final.
- Compatibility/schema notes accurate.
- No generated credentials, private mappings or customer data in examples/artifacts.
- Create/push the matching immutable tag only after the above checks.