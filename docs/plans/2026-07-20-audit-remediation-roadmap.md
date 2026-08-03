# Audit remediation roadmap

**Status:** Proposed
**Date:** 2026-07-20
**Branch / worktree:** `grok/audit-fix-plans` @
`/Users/bledy/workspace/repos/timezone-converter-audit-fix-plans`
**Source:** full repository audit (session 2026-07-20)

## Goal

Close every finding from the audit: correctness/UX, packaging honesty,
hygiene, CLI robustness, CI/CD supply-chain, and (as a separate later
track) optional product features. Each phase is a shippable PR with its
own tests, 100% coverage maintained, and Conventional Commits.

## Non-goals (this roadmap)

- Rewriting DST day construction (already correct).
- Replacing Rich, argparse, or the view inheritance model.
- Force-deleting remote stale branches without explicit owner review.
- Pinning every third-party Action to a full commit SHA on day one if
  Dependabot is added first (Plan E chooses Dependabot + selective pins).

## Global constraints (every plan)

- Python 3.9 syntax only (`List`/`Optional`/`Union`; no `X | Y`, no `match`).
- Package code stays strict-MyPy clean; tests may be loosely typed.
- CLI flag or behavior changes update **parser, dispatch, views, tests,
  README, tox smokes, and AGENTS.md** together.
- DST-sensitive code requires spring-forward **and** fall-back tests
  (and half-hour zones when hour selection changes).
- Coverage stays **100%** (`coverage run -m pytest && coverage report`).
- Run `pre-commit run --all-files` before claiming done.
- No AI co-author trailers; no force-push; feature work only in
  external worktrees per global `AGENTS.md`.

## PR stack (recommended order)

| PR | Plan file | Title (approx.) | Risk | Depends on |
|----|-----------|-----------------|------|------------|
| 1 | `2026-07-20-pr1-hygiene-docs.md` | chore: hygiene, ignore files, docstring drift | Low | — |
| 2 | `2026-07-20-pr2-packaging.md` | fix: packaging markers and module entry | Low | — (parallel OK with 1) |
| 3 | `2026-07-20-pr3-cli-robustness.md` | fix: CLI robustness (version, modes, exits) | Medium | 1 optional |
| 4 | `2026-07-20-pr4-hour-wall-clock.md` | fix: `--hour` means local wall clock | **High (behavior)** | 3 recommended |
| 5 | `2026-07-20-pr5-ci-release.md` | ci: Dependabot, release job graph, Docker smoke | Medium | 1 (dockerignore) |
| 6 | `2026-07-20-pr6-product-enhancements.md` | feat: date/local/format + ambiguous short names | Product | 4 recommended |

PRs 1 and 2 can merge in either order or as a single combined PR if
preferred. PR 4 is intentionally last among correctness fixes because it
is user-visible. PR 6 is optional product work called out in the audit
as “later”; include only after 1–5 are done unless a specific feature
is requested earlier.

## Audit finding → plan map

### Fixes (bugs / incorrect behavior)

| Finding | Plan / PR |
|---------|-----------|
| `--hour N` is Nth real hour, not local wall `N:00` on DST days | PR 4 |
| Docstring still mentions `--single` | PR 1 |
| Unknown-timezone exit streams inconsistent (`SystemExit` str vs Rich+1) | PR 3 |
| `build_parser()` hard-requires `tzdata` dist on every parse | PR 3 |
| Combined modes silently prefer list > search > comparison | PR 3 |
| Bare `--search` falls through to help | PR 3 |

### Improvements

| Finding | Plan / PR |
|---------|-----------|
| Missing `py.typed` despite `Typing :: Typed` | PR 2 |
| No `__main__.py` (`python -m timezone_converter` fails) | PR 2 |
| `ArgumentError(None, …)` → `ArgumentTypeError` | PR 3 |
| Dead `setup-cfg-fmt` pre-commit hook | PR 1 |
| Expand `.gitignore` (coverage artifacts, etc.) | PR 1 |
| `.dockerignore` has `test` not `tests` | PR 1 |
| `[project.optional-dependencies] dev` | PR 2 |
| Beta → Production/Stable classifier | PR 2 (decision callout) |
| Document `tzconv` / `python -m` in AGENTS | PR 1 |
| Stale local editable install | note only (local hygiene) |

### Additions (process / product)

| Finding | Plan / PR |
|---------|-----------|
| Dependabot for Actions / pre-commit / pip | PR 5 |
| Safer release job graph (no half-publish) | PR 5 |
| Docker smoke after image build | PR 5 |
| CHANGELOG.md process | PR 5 (lightweight) + RELEASE.md |
| SECURITY.md | PR 5 |
| `--date`, `--local`, `--format`, ambiguous short-name warn | PR 6 |
| Python 3.14 matrix | PR 5 or follow-up when ready |

### Deletions / cleanup

| Finding | Plan / PR |
|---------|-----------|
| Remove `setup-cfg-fmt` hook | PR 1 |
| Drop or keep `develop` CI branch trigger | PR 5 (document choice: keep unless confirmed unused) |
| Dead `returncode is None` branch | PR 3 (keep safety + test, or tighten types—plan chooses keep) |
| Remote stale branches | **Out of band** — list in PR 5 notes; do not auto-delete |

### Security

| Finding | Plan / PR |
|---------|-----------|
| Image includes `tests/` | PR 1 |
| Unpinned Action tags | PR 5 (Dependabot first) |
| PyPI before Docker failure | PR 5 |
| Base image digest pin | PR 5 (optional stretch; tag + Dependabot default) |

### Performance

No code changes planned. Import ~80 ms is acceptable. Revisit only if
profiling shows a regression after PR 2/3 map changes (none expected).

### Testing gaps closed by plans

| Gap | Plan |
|-----|------|
| `--hour` on DST days | PR 4 |
| CLI unknown zone exit/stream | PR 3 |
| Mode mutual exclusion | PR 3 |
| Bare `--search` | PR 3 |
| Fall-back highlight assert | PR 4 (or PR 3 if isolated) |
| `tzconv` / `__main__` smoke | PR 2 tox |
| Docker smoke in CI | PR 5 |

## Versioning and release

- **Do not** bump `project.version` inside hygiene/docs-only PRs.
- PR 4 (`--hour` behavior) is a **behavior change**: include in the
  next minor (e.g. `0.17.0`) release notes; do not ship silently in a
  patch if users rely on index semantics (unlikely but document it).
- PR 6 features → minor version bumps as shipped.
- Follow `RELEASE.md` for tagging (`vX.Y.Z` or `X.Y.Z`).

## Execution guidance

1. Create one external worktree/branch per PR from latest `origin/main`
   (or restack Graphite-style if preferred):
   `grok/audit-hygiene`, `grok/audit-packaging`, etc.
2. Prefer TDD for behavioral changes (PR 3, PR 4, PR 6).
3. After each PR: coverage 100%, pre-commit clean, open/update PR,
   mark ready when checks pass.
4. Update this roadmap **Outcome** section when a PR merges.

## Outcome

_Not yet implemented. Fill on completion: dates, PR URLs, deviations,
validation, remaining work._
