# Release checklist

This project uses a static package version in `pyproject.toml`. Release tags
must match that version exactly, either as `X.Y.Z` or `vX.Y.Z`.

## Before creating the release

- Update `project.version` in `pyproject.toml`.
- Update user-facing docs when behavior or CLI flags changed.
- When adding a CLI flag, add a smoke-test invocation to the tox `commands`
  list in `pyproject.toml`.
- Run `pre-commit run --all-files`.
- Run `coverage run -m pytest && coverage report`.
- Run any Docker command you want to verify locally, for example
  `docker build -t timezone-converter:local .`.

## Create the release

- Commit the release changes.
- Tag the commit with the matching version, for example `v0.15.0`.
- Create and publish a GitHub Release from that tag.

## Automated publishing

Publishing the GitHub Release triggers `.github/workflows/deployment.yml`.
That workflow:

- validates the release tag against `pyproject.toml`;
- targets the `release` GitHub Actions environment;
- runs the test suite;
- builds the wheel and source distribution;
- publishes to PyPI with trusted publishing;
- builds and pushes Docker images for `linux/amd64` and `linux/arm64`.

Docker Hub receives these tags for non-prerelease semver releases:

- exact version, for example `0.15.0`;
- minor version, for example `0.15`;
- `latest`.

Prereleases do not update `latest`.

## PyPI trusted publishing

The workflow does not use a `PYPI_API_TOKEN`. Configure this repository as a
trusted publisher for the `timezone-converter` project in PyPI, with:

- owner: `ibLeDy`;
- repository: `timezone-converter`;
- workflow: `deployment.yml`;
- environment: `release`.

Also create a `release` environment in the repository's GitHub Actions settings.
Use environment protection rules there if PyPI publishing should require manual
approval or be restricted to specific maintainers.
