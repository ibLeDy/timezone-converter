# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A CLI tool (published to PyPI as `timezone-converter`) that prints a full day of the local timezone side-by-side with one or more foreign timezones, rendered with `rich`. Entry point: `timezone_converter.main:main` (declared under `[project.scripts]`).

## Commands

- Install for development: `pip install -e .` (then `requirements-dev.txt`: `pytest`, `coverage`, `covdefaults`)
- Run the CLI: `timezone-converter <timezone> [<timezone> ...]` or `python -m timezone_converter.main`
- Lint/format/type-check (all via pre-commit — black, flake8 max-line-length=88, mypy, reorder-python-imports, add-trailing-comma): `pre-commit run --all-files`
- Full test matrix (py39–py313): `tox`. Note: tox's `[testenv] commands` runs the CLI with various args as smoke tests (see `pyproject.toml`), it does **not** run pytest. CI (`.github/workflows/integration.yml`) runs `tox` on Linux/macOS/Windows.
- Run the tests: `pytest` (test files use the `*_test.py` suffix, enforced by the `name-tests-test` pre-commit hook). Single test: `pytest tests/comparison_view_test.py::test_name`. Coverage is configured via `covdefaults` (100% required): `coverage run -m pytest && coverage report`.

## Conventions

- mypy runs in strict mode (`disallow_untyped_defs`, `disallow_any_generics`, etc.) — all functions need full type annotations. Use `typing.List`/`Optional`/`Union` (not `list[...]`/`X | None`) because the minimum supported version is Python 3.9.
- black is configured with `--skip-string-normalization`; the codebase uses single quotes. Match that.
- Minimum Python is 3.9 — don't use newer syntax (e.g. `match`, `X | Y` type unions, `str.removeprefix` is fine but built-in generics in annotations are not).

## Architecture

Three "view" classes drive the three mutually-exclusive modes, dispatched in `main.main()` based on parsed args (`--list` → `--search` → positional `timezone` → help). Each view subclasses `Helper` and exposes a single `print_*()` method returning an `int` exit code.

- `helper.py` — `Helper` base class. Owns the central data structure `timezone_translations`: a class-level dict mapping the lowercased last path segment of every `pytz.all_timezones` entry (e.g. `new_york`) to its canonical name (e.g. `America/New_York`). All user input is resolved through this dict. Also wraps all output via `_print_with_rich`.
- `comparison_view.py` — `ComparisonView`: the default mode. Computes local midnight, converts it to each foreign timezone, then renders a 24-row (or single-hour) table. `--zone` adds tz abbreviation to headers, `--order` sorts columns by UTC-offset distance from local, `--single` limits to one hour, current hour is highlighted blue. Unknown timezones raise `SystemExit` after showing `difflib.get_close_matches` suggestions.
- `list_view.py` — `ListView`: `--list [LETTERS]` renders all timezones grouped by first letter into `rich` panels.
- `search_view.py` — `SearchView`: `--search WORD` fuzzy-matches against `timezone_translations` via `difflib.get_close_matches`.
- `main.py` — argparse setup (`build_parser`) and dispatch. Custom arg types `_single_hour` (validates 0–23) and `_list_letter` (alpha-only).
- `constants.py` — `VERSION` read from installed package metadata via `importlib.metadata`.

When adding a CLI flag: add it in `build_parser()`, dispatch in `main()`, and add a smoke-test invocation to the tox `commands` list in `pyproject.toml`.
