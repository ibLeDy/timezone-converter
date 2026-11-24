# Release checklist

The package version in `pyproject.toml` and signed tag must agree. The prepared
release is 1.0.0, requires Python 3.11+, and remains unpublished until the owner
approves an exact final main commit and `v1.0.0`.

## Validate the candidate

1. Refresh #117 from current main with a normal merge; preserve all commits.
   #118/#120/#123/#121/#124 are already merged. #119 is feature work for 1.1;
   issue #85 is post-1.0 visual polish.
2. Install `.[dev]`, build and Twine in an isolated feature-worktree environment.
   Confirm installed metadata reports 1.0.0 and `Requires-Python: >=3.11`.
3. Run all pre-commit hooks and coverage-backed tests (100% statements/branches).
4. Run tox sequentially for Python 3.11-3.15. Parallel environments share the
   coverage data file. Require fresh Linux/macOS/Windows CI on all five versions.
5. Build wheel and sdist, run `twine check`, then install each independently
   outside the checkout. Exercise both console scripts and both module forms.
6. Build and smoke test Docker for amd64 and arm64; require both native CI jobs.
   Verify the image's actual interpreter version. Use writable temporary output
   if running the full coverage suite as the non-root image user.
7. Exercise spring/fall DST (23/25 rows), repeated/skipped hours, JSON/error
   routing, fuzzy suggestions, and narrow/wide Rich layouts. Invalid markup,
   conversion overflow, and nonexistent local dates must fail cleanly, with no
   traceback or partial JSON; comparison-only flags without a zone must exit 2.

## Require every CI check

`docs/tasks/1.0.0-required-checks.json` contains the complete strict 18-check
policy: Python 3.11-3.15 on Linux/macOS/Windows (15), native Docker amd64/arm64
(2), and pre-commit.ci (1). Bind Actions checks to app 15368 and pre-commit.ci
to app 68672. Verify those identities and exact names against the final PR.

The earlier main policy required only twelve 3.10-3.13 jobs. The new policy
removes the three 3.10 checks and adds 3.14, 3.15, both Docker architectures,
and pre-commit.ci. Preserve strict mode, signatures, review requirements,
force-push/deletion controls, and administrator settings.

1. Back up the current protection response outside the checkout.
2. Wait for all eighteen candidate checks to pass.
3. Apply only the reviewed required-check subresource:

   ```sh
   gh api --method PATCH \
     repos/ibLeDy/timezone-converter/branches/main/protection/required_status_checks \
     --input docs/tasks/1.0.0-required-checks.json
   ```

4. Read protection back and compare the check names, app IDs and strict mode.
   Confirm every unrelated protection field matches the backup.
5. Mark the completed PR ready, then use a normal merge commit after maintainer
   approval. Require the full matrix and Docker CI on the resulting main commit.

## Verify publishing access and release approval

> [!WARNING]
> 🟠 WARNING — Secret names and historical deployments do not establish current
> publishing access. Verify both services without uploading a test release.

1. In authenticated PyPI project settings, confirm the trusted publisher:
   owner `ibLeDy`, repository `timezone-converter`, workflow `deployment.yml`,
   environment `release`. OIDC publishing does not use `PYPI_API_TOKEN`.
2. Confirm Docker Hub publishing access for `bledy/timezone-converter` and the
   token used by GitHub's `DOCKERHUB_TOKEN`. A different local login or public
   image pull does not verify that stored token's write permission.
3. Review `docs/tasks/1.0.0-release-environment.json`: require owner review for
   deployment through the `release` environment. Allow self-review because this
   is a solo-maintainer repository; leave branch-review requirements unchanged.
   Read settings back after applying it. Existing secrets are preserved.
4. Verify 1.0.0 is absent from GitHub and PyPI. Replace the changelog's
   `Unreleased` marker with the actual Europe/Madrid publication date in a
   reviewed commit and rerun the final checks. Do not invent a release date
   during preparation.
5. Obtain explicit publication approval identifying the final main SHA and
   signed tag `v1.0.0`.

## Publish the approved release

> [!CAUTION]
> 🔴 DANGER — Publishing a GitHub Release starts Docker/PyPI publication.
> PyPI permanently consumes the version number, and Docker's `latest` and
> minor-version tags move. Obtain explicit approval immediately before this
> operation; there is no complete rollback.

1. Create a signed `v1.0.0` tag at the approved main SHA and push that tag.
2. Publish the GitHub Release from the tag using its changelog section.
3. Watch `deployment.yml`: tag/version validation and tests run first; Docker
   builds and smoke-tests amd64 before pushing amd64/arm64; PyPI builds and
   uploads wheel/sdist only after Docker succeeds.
4. Approve each deployment after checking its exact tag and commit. Docker and
   PyPI each use the `release` environment, so a reviewer gate applies twice.
5. Verify the GitHub Release commit; PyPI 1.0.0 metadata, artifacts and clean
   installs; and Docker manifests/tags for both architectures. Confirm
   `Requires-Python: >=3.11` and correct installed CLI versions.

If a job fails, identify the last successful publication before retrying.
Never blindly retry a successful PyPI upload. A yank, tag replacement, or
corrective release requires a separate explicit decision.

## ⚠️ Attention and behavior changes

> [!CAUTION]
> 🔴 DANGER — Publication requires explicit approval for the final SHA/tag;
> merging the preparation PR is not publication approval.

> [!WARNING]
> 🟠 WARNING — Publishing access and release-review settings must be verified
> before tagging. Keep the changelog marked Unreleased until publication prep.

> [!IMPORTANT]
> 🔵 BEHAVIOR CHANGE — Python 3.11+ is required; the full CI matrix is
> 3.11-3.15. CLI validation and error routing change as documented in CHANGELOG.
