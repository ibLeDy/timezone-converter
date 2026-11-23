Status: Complete

# Repair red integration builds

## Scope and ownership

Continue PR #123 on `claude/serene-gates-3g99cn` in the persistent
`repair-red-builds` worktree. The existing PR owns the seasonal regression;
no competing branch or PR is needed.

Claimed files: `tests/comparison_view_test.py`,
`.github/workflows/integration.yml` (Linux test runner only), and this note.
PRs #117 and #119 also touch the workflow and tests for release/features;
the runner pin and seasonal test are independent of their intended changes.
Leave their branches and the existing release worktree untouched.

## Confirmed failures

- PRs #121 and #124 fail the local-column regression because it expects
  `CEST` while using the real clock, which currently produces `CET`.
- Run 41520296890, job 125534280063 fails before tests: Python 3.9 is
  unavailable for Ubuntu 26.04 after `ubuntu-latest` moved.
- Both Docker architectures pass on the two failing PRs.

## Repair and acceptance

1. Exercise the TZ local-column contract at fixed summer and winter instants,
   checking the abbreviation and displayed local date/hour together.
2. Pin the Linux Python test runner to Ubuntu 24.04 while retaining the full
   supported Python 3.9-3.14 matrix and all existing checks.
3. Run coverage (100%), all pre-commit hooks, sequential tox across every
   available supported interpreter, and wheel/sdist validation.
4. Push the existing PR and verify its Linux/macOS/Windows matrix and native
   Docker builds. Mark it ready only after all relevant checks pass.
5. Record the remaining merge and downstream PR refresh steps. Merging or
   publishing a release is outside this repair's authorization.

## Validation and handoff

Validated on 2026-11-23 at code commit `9ba8de6`:

- 156 tests pass with 100% statement and branch coverage on each local
  interpreter: Python 3.9.6, 3.10.20, 3.11.15, 3.12.13, 3.13.14, and 3.14.6.
- Sequential tox passes all six environments and their 23 CLI smoke commands.
- Every configured pre-commit hook passes, including Black, Flake8, and MyPy.
- Wheel and sdist build successfully and both pass Twine checks.
- Integration run 45165500890 passes all 20 jobs: Linux/macOS/Windows on
  Python 3.9-3.14, plus native amd64/arm64 Docker builds and smoke tests.
  pre-commit.ci also passes. Linux Python 3.9 succeeds on Ubuntu 24.04.

The fixes are ready for PR review. Refresh #121 and #124 by merging this
repair branch into their existing branches, preserving both histories, then
verify their checks and mark completed PRs ready. Use separate persistent
`refresh-hook-builds` and `refresh-docker-builds` worktrees. These refreshes
change neither the hook pins nor the Docker base selected by those PRs.

Merge #123 into main before the two bot PRs so their diffs reduce to their
original dependency updates. GitHub merge and release publication remain
separate owner decisions. The existing release worktree and #117/#119
branches were preserved.
