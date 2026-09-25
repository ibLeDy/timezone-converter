# AGENTS.md

## Project

Timezone Converter is a cross-platform Python 3.10+ Rich CLI published as
`timezone-converter`, with entry point `timezone_converter.main:main`. Timezone
data comes from `zoneinfo` plus `tzdata`; avoid platform-specific behavior.

## Commands

- Install: `pip install -e ".[dev]"` (the `dev` extra mirrors
  `requirements-dev.txt`, which CI still installs directly)
- Run: `timezone-converter` or `tzconv` `<timezone> [<timezone> ...]` or
  `python -m timezone_converter`
- Test: `pytest` (or `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` when global
  plugins interfere)
- Required coverage: `coverage run -m pytest && coverage report` (100%)
- All hooks: `pre-commit run --all-files`
- Python 3.10-3.14 matrix and CLI smoke tests: `tox`

`tox` runs coverage-backed tests and the smoke commands in `pyproject.toml`.

## Architecture and correctness

`main.main()` dispatches `--list`, `--search`, comparisons, then help.
`helper.py` owns timezone lookup and Rich output; view `print_*()` methods return
integer exit codes.

- Build comparisons from timezone-aware instants. DST means a local day may
  contain 23, 24, or 25 real hours; never freeze one UTC offset or assume every
  day has 24 instants. Add spring-forward and fall-back tests when changing
  table construction, conversion, ordering, highlighting, or hour selection.
- Preserve short names such as `new_york`, exact paths such as
  `America/New_York`, canonical access to ambiguous short names, useful fuzzy
  suggestions, and nonzero exits for unknown zones.
- The local zone is `ComparisonView.local_zone`: `--local` first, then `TZ`
  via `helper.local_timezone()` when it names an IANA zone, else `None`,
  meaning the machine's own zone through the `_to_local` seam. Resolve `TZ`
  via `zoneinfo`, never the C library, which needs the OS timezone database
  that slim images omit and Windows lacks, and silently reads
  `Europe/Madrid` as a POSIX rule at UTC+0 when that lookup fails.
- Route normal output through `Helper._print_with_rich`, and errors through
  `Helper._print_error_with_rich`, which writes to stderr. The one exception is
  machine-readable output (`--format json`), which uses `Helper._print_plain`
  because Rich's wrapping and highlighting would corrupt it. Manually exercise
  Rich layout changes and update stale `.github/assets/` examples with
  `python scripts/generate_assets.py`, then review the diff before committing.

## Compatibility and coordinated changes

- Python 3.10 is the floor: `X | Y` unions, built-in generics such as
  `list[str]`, and `match` are available; 3.11+ features such as
  `typing.Self`, `except*` and `tomllib` are not, and MyPy checks against 3.10
  to catch them. Existing code still spells annotations with `typing.List`,
  `Optional` and `Union`, so match the style of the file you are editing.
  Package code is checked by strict MyPy.
- A CLI flag change must update parser, dispatch, affected view, tests, README
  usage, and tox smoke commands together. Preserve view exit-code contracts.
- Follow `RELEASE.md` for releases; the project version and release tag must
  match.

## CI

`integration.yml` runs the `tox` matrix on pushes to `main` and on pull
requests targeting `main`. It no longer triggers on `develop`: that branch
is fully merged into `main` and has had no unique commits since January
2025, so the trigger only ever produced duplicate runs. Restore it in
`integration.yml` if `develop` is ever revived. It also builds the Docker
image and runs `scripts/smoke_test_image.sh` against it, the same script
`deployment.yml` runs before pushing an image.

`deployment.yml` runs on a published release; see `RELEASE.md` for its job
order. Dependabot tracks GitHub Actions weekly, and pip and the Docker base
image monthly; pre-commit.ci opens its own monthly hook autoupdate.
