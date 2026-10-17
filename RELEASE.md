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
- Run `tox` sequentially for every supported Python version (parallel tox
  environments share the coverage file). Require 100% coverage.
- Build the wheel and sdist with `python -m build`, run
  `python -m twine check dist/*`, and install each artifact in a fresh
  environment outside the checkout. Exercise `timezone-converter`, `tzconv`,
  `python -m timezone_converter`, and `python -m timezone_converter.main`.
- Build and run `scripts/smoke_test_image.sh IMAGE` for both `linux/amd64`
  and `linux/arm64`, and require green native CI jobs for both architectures.
- Manually verify spring-forward and fall-back dates, repeated/skipped hours,
  JSON parsing with empty stdout on errors, unknown-zone suggestions, and Rich
  tables at narrow and wide terminal widths.
- Require the complete supported Python/OS matrix, Docker smoke tests and
  configured hooks on the combined release candidate, then on the final main
  commit. Separate green PRs do not establish a green combined candidate.
- Confirm Docker Hub publishing access and the current PyPI trusted publisher
  tuple below without printing secrets. Secret names and old successful runs
  do not prove current authorization.

## 1.0.0 merge and protection gate

The prepared scope is #118 (native Docker smoke tests), #120 (read-only
integration permissions), and #117 (release contract, changelog, correctness
fixes and this checklist). #117 contains normal local merges of #118/#120 for
combined validation; their commits are preserved. Defer #119 to 1.1 and #85
until after 1.0. Keep #103-#107, #116 and #121 separate from this candidate.

> [!CAUTION]
> 🛑 BLOCKER — Obtain explicit maintainer approval before GitHub merges or
> branch-protection changes. Keep strict required checks and signed commits;
> never use an administrator bypass to merge missing checks.

After approval, use this sequence, checking each PR head has not changed:

1. Merge #118 with a normal merge commit. Wait for main's checks.
2. Merge updated main into #120 without rebasing. Wait for its checks, then
   merge #120 with a normal merge commit. Wait for main's checks.
3. Merge updated main into #117 without rebasing. Wait for the entire candidate
   matrix, both Docker jobs and pre-commit.ci.
4. Re-read protection and compare it with the audited settings. Apply only
   the approved required-status-check payload in
   `docs/tasks/1.0.0-required-checks.json` using the required-check subresource:

   ```sh
   gh api --method PATCH \
     repos/ibLeDy/timezone-converter/branches/main/protection/required_status_checks \
     --input docs/tasks/1.0.0-required-checks.json
   ```

   It removes `linux (3.9)`, `macos (3.9)`, and `windows (3.9)`, retains the
   existing 3.10-3.13 jobs, and requires the three 3.14 jobs, `docker (amd64)`,
   `docker (arm64)`, and `pre-commit.ci - pr`: 18 checks. Actions checks remain
   bound to GitHub Actions app 15368; the external pre-commit status uses
   `app_id: 68672`, verified as the `pre-commit-ci` GitHub App. `strict: true`
   remains enabled. This subresource leaves review,
   signature, force-push, deletion and administrator settings untouched.
5. Verify protection, mark #117 ready once its material gates are resolved,
   and merge it with a normal merge commit. Wait for final main's full CI.
6. Recheck version 1.0.0, the changelog date, unpublished GitHub/PyPI state,
   publishing access, and the exact final main SHA before requesting publication.

The changelog is dated for the intended release day, 2026-10-17. If publication
happens later, update it in a reviewed commit to the actual Europe/Madrid date
and pass the final checks again before tagging. A preparation date is not proof
that the release has happened.

## Create the release

> [!CAUTION]
> 🔴 DANGER — Publishing the GitHub Release starts Docker/PyPI publication
> immediately. Obtain explicit approval for the final commit and tag before
> this step; the PyPI version cannot be reclaimed.

- Commit the release changes.
- Obtain explicit publication approval identifying the final main SHA and
  tag `v1.0.0`. Publishing changes Docker tags and permanently consumes the PyPI
  version; it has no complete rollback.
- Create the matching signed tag at that approved SHA and push it:

  ```sh
  git tag -s v1.0.0 APPROVED_MAIN_SHA -m 'Release 1.0.0'
  git push origin refs/tags/v1.0.0
  ```

  Replace `APPROVED_MAIN_SHA` with the verified approved commit first.
- Create and publish a GitHub Release from that tag, using that version's
  `CHANGELOG.md` section as the release body.

## Automated publishing

Publishing the GitHub Release triggers `.github/workflows/deployment.yml`.
That workflow runs three jobs in order, each one gating the next:

1. `test` validates the release tag against `pyproject.toml` and runs the
   test suite with coverage.
2. `docker` builds a `linux/amd64` image, loads it, and runs
   `scripts/smoke_test_image.sh` against it (the packaged CLI entrypoint, and
   that `TZ` sets the `LOCAL` column) before building and pushing the
   multi-arch `linux/amd64` and `linux/arm64` images. Targets the `release`
   environment.
3. `pypi` builds the wheel and source distribution and publishes to PyPI
   with trusted publishing. Targets the `release` environment, and needs
   `docker` to have succeeded.

PyPI publishing goes last deliberately: a PyPI release cannot be taken back,
since a yanked version still burns that version number, whereas a Docker tag
can be replaced. The cost of that ordering is that a Docker Hub outage blocks
the PyPI publish. To release anyway, re-run the workflow once Docker Hub
recovers.

Both `docker` and `pypi` target the `release` environment. Docker uses the
Docker Hub secrets; PyPI uses the environment-bound OIDC identity, without a
PyPI API token. If you add manual approval to that environment,
expect to approve twice per release.

Docker Hub receives these tags for non-prerelease semver releases:

- exact version, for example `1.0.0`;
- minor version, for example `1.0`;
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


## Verification after publishing

1. Watch the deployment run for `v1.0.0`; verify test, Docker and PyPI jobs each
   succeed. Do not rerun a successful PyPI upload blindly.
2. Confirm PyPI metadata says 1.0.0 with `Requires-Python: >=3.10`; install the
   released wheel and sdist in clean environments and check both entry points.
3. Inspect Docker Hub's 1.0.0 manifest for amd64 and arm64, smoke test both,
   and confirm the `1.0` and `latest` tags refer to this release.
4. Confirm the GitHub Release points to the approved commit and has the
   consolidated changelog as its body.

If publication fails, identify the last successful job before retrying. Before
PyPI upload, fix the cause and rerun the failed jobs after checking what was
already published. After a PyPI upload, the version cannot be reused: a yank
can stop normal installation but cannot erase it. Any yank, tag replacement,
or corrective release needs a separate explicit decision.

## ⚠️ Attention and behavior changes

> [!CAUTION]
> 🔴 DANGER — Publishing a GitHub Release triggers external Docker/PyPI writes.
> Obtain explicit approval immediately before publication. PyPI versions cannot
> be reclaimed; Docker's `latest` and minor tags change for a stable release.

> [!WARNING]
> 🟠 WARNING — Verify current publishing authorization before release. The
> `release` environment currently has no approval rules, so publishing itself
> starts deployment without a later human checkpoint.

> [!IMPORTANT]
> 🔵 BEHAVIOR CHANGE — 1.0.0 requires Python 3.10+ and changes CLI validation
> and error routing. Read the changelog's migration notes before upgrading.
