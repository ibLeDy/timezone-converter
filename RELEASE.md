# Release checklist

This project uses a static package version in `pyproject.toml`. Release tags
must match that version exactly, either as `X.Y.Z` or `vX.Y.Z`.

## Before creating the release

- Update `project.version` in `pyproject.toml`.
- Update `CHANGELOG.md`: give the section for this version its release date,
  and make sure every user-facing change since the last release is listed.
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
- Create and publish a GitHub Release from that tag, using that version's
  `CHANGELOG.md` section as the release body.

## Automated publishing

Publishing the GitHub Release triggers `.github/workflows/deployment.yml`.
That workflow runs three jobs in order, each one gating the next:

1. `test` validates the release tag against `pyproject.toml` and runs the
   test suite with coverage.
2. `docker` builds a `linux/amd64` image, loads it, and smoke-tests the
   packaged CLI entrypoint (`--version`, a comparison, and `--list`) before
   building and pushing the multi-arch `linux/amd64` and `linux/arm64`
   images. Targets the `release` environment.
3. `pypi` builds the wheel and source distribution and publishes to PyPI
   with trusted publishing. Targets the `release` environment, and needs
   `docker` to have succeeded.

PyPI publishing goes last deliberately: a PyPI release cannot be taken back,
since a yanked version still burns that version number, whereas a Docker tag
can be replaced. The cost of that ordering is that a Docker Hub outage blocks
the PyPI publish. To release anyway, re-run the workflow once Docker Hub
recovers.

Both `docker` and `pypi` target the `release` environment because each needs
its own credentials from it. If you add manual approval to that environment,
expect to approve twice per release.

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
