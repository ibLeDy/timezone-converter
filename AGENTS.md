# AGENTS.md

## Project

Timezone Converter is a cross-platform Python 3.9+ Rich CLI published as
`timezone-converter`, with entry point `timezone_converter.main:main`. Timezone
data comes from `zoneinfo` plus `tzdata`; avoid platform-specific behavior.

## Commands

- Install: `pip install -e .` and `pip install -r requirements-dev.txt`
- Run: `timezone-converter <timezone> [<timezone> ...]` or
  `python -m timezone_converter.main`
- Test: `pytest` (or `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` when global
  plugins interfere)
- Required coverage: `coverage run -m pytest && coverage report` (100%)
- All hooks: `pre-commit run --all-files`
- Python 3.9-3.13 matrix and CLI smoke tests: `tox`

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
- Route normal output through `Helper._print_with_rich`. Manually exercise Rich
  layout changes and update stale `.github/assets/` examples.

## Compatibility and coordinated changes

- Keep Python 3.9 syntax: use `typing.List`, `Optional`, and `Union`, not
  built-in generic annotations, `X | Y`, or `match`. Package code is checked by
  strict MyPy.
- A CLI flag change must update parser, dispatch, affected view, tests, README
  usage, and tox smoke commands together. Preserve view exit-code contracts.
- Follow `RELEASE.md` for releases; the project version and release tag must
  match.
