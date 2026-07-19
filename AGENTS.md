# AGENTS.md

## Project overview

Timezone Converter is a Python 3.9+ CLI published to PyPI as
`timezone-converter`. It renders a local calendar day beside foreign timezones
with Rich. Its entry point is `timezone_converter.main:main`.

It supports macOS, Windows, and Linux through `zoneinfo` plus `tzdata`; avoid
POSIX-only APIs, machine-specific paths, and shell-dependent behavior.

## Commands

- Install: `pip install -e .` and `pip install -r requirements-dev.txt`
- Run: `timezone-converter <timezone> [<timezone> ...]` or
  `python -m timezone_converter.main`
- Test: `pytest`
- Test without globally installed pytest plugins:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest`
- Single test: `pytest tests/comparison_view_test.py::test_name`
- Coverage: `coverage run -m pytest && coverage report` (100% required)
- Format, lint, and type-check: `pre-commit run --all-files`
- Python 3.9-3.13 matrix plus CLI smoke tests: `tox`

`tox` runs the coverage-backed test suite before the CLI smoke commands listed
in `pyproject.toml`. CI runs that matrix on Linux, macOS, and Windows.

## Architecture

`main.main()` dispatches mutually exclusive modes in this order: `--list`,
`--search`, positional timezone comparison, then help.

- `timezone_converter/main.py`: argparse, custom argument types, and dispatch.
- `timezone_converter/helper.py`: short-name and canonical-path resolution,
  discovery/search data, and the shared Rich output wrapper.
- `timezone_converter/comparison_view.py`: DST-aware comparison tables.
- `timezone_converter/list_view.py`: timezone groups for `--list`.
- `timezone_converter/search_view.py`: fuzzy results for `--search`.
- `timezone_converter/constants.py`: installed-package version lookup.
- `tests/`: module-level tests; filenames must end in `*_test.py`.

Each view subclasses `Helper` and exposes one `print_*()` method returning an
integer exit code.

## Timezone and CLI correctness

- Build comparisons from aware instants. A local calendar day may contain 23,
  24, or 25 real hours across DST changes; never freeze one UTC offset or use a
  fixed `range(24)` for a complete day.
- Add spring-forward and fall-back tests when changing date conversion, table
  construction, ordering, single-hour selection, or current-hour highlighting.
- Preserve short names such as `new_york` and exact canonical paths such as
  `America/New_York`. Ambiguous short segments must remain reachable through
  canonical paths.
- Unknown zones must keep useful fuzzy suggestions and a nonzero exit.
- Route normal output through `Helper._print_with_rich`. Avoid debug output,
  prompts, network access, and machine-specific values in CLI output.
- Manually exercise commands affected by Rich layout or styling changes. Update
  `.github/assets/` only when its examples no longer match current output.

## Python conventions

- Keep Python 3.9 compatibility: use `typing.List`, `Optional`, and `Union`, not
  built-in generic annotations, `X | Y`, or `match`.
- Package functions require complete annotations under the strict MyPy config.
  Do not add broad type ignores or weaken checks to accommodate a change.
- Match Black's `--skip-string-normalization` configuration: single-quoted
  strings and 88-character lines.
- Import ordering, trailing commas, formatting, and test naming are enforced by
  pre-commit; fix the underlying issue rather than bypassing a hook.

## Change and release checklist

When adding or changing a CLI flag, update the parser, dispatch, affected view,
tests, README usage, and tox smoke commands together. Preserve the view exit-code
contract.

`pyproject.toml` is authoritative for metadata, dependencies, entry points,
build contents, Python versions, and tox commands. Do not add or upgrade a
dependency without approval. Never commit build artifacts, environments,
caches, coverage data, or `__pycache__` files.

Follow `RELEASE.md`; the static project version and GitHub release tag must
match. Publishing a GitHub Release tests and publishes the PyPI distributions
and multi-platform Docker image.
