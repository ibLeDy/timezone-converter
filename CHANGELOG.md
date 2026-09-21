# Changelog

All notable user-facing changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases before `1.0.0` are not backfilled here; see the
[GitHub releases](https://github.com/ibLeDy/timezone-converter/releases) for
their notes.

## [Unreleased]

### Added

- `--date YYYY-MM-DD` / `-D`, to compare a local calendar day other than
  today. The day is built from that date's own timezone rules, so a past or
  future DST transition day still shows its real 23 or 25 hours rather than
  today's offset applied to another date. Combines with `--hour`, which
  still means the wall-clock hour on the chosen day.

## [1.0.0] - 2026-09-20

First stable release. Everything below has been sitting on `main` since
`v0.16.1` without being published, so this is the release that actually ships
it.

**Upgrading from `0.16.1`:** every entry marked **Breaking** below matters if
you script against this tool. Two of them are about `--hour`; the rest are
cases where the CLI used to succeed quietly and now reports an error, plus
the move of error output from stdout to stderr.

### Added

- `tzconv` as a short console-script alias for `timezone-converter`. Both
  entry points are installed and behave identically.
- `--difference` / `-d`, which appends each foreign column's signed hour
  offset from your local timezone to its header, such as `+9.5h` or `-5h`.
  Combined with `--zone` the difference follows the abbreviation, e.g.
  `AMERICA/TIJUANA (PST) -8h`. The `LOCAL` column is excluded, since its
  offset from itself is always zero.
- `--version` now reports the version of the installed `tzdata` database
  alongside the package version, e.g.
  `timezone-converter 1.0.0 (tzdata 2026.4)`, so a timezone-data question can
  be answered without inspecting the environment.
- NumPy-style docstrings across the public API.
- `python -m timezone_converter` now works. Only the longer
  `python -m timezone_converter.main` did before; both are supported.
- A `py.typed` marker (PEP 561) ships in the wheel and sdist, so the
  `Typing :: Typed` classifier is true and type checkers actually use the
  package's annotations instead of treating it as untyped.
- A `dev` extra, so `pip install -e ".[dev]"` installs the development
  dependencies that previously only existed in `requirements-dev.txt`.
- `scripts/generate_assets.py`, which regenerates the README screenshots
  under `.github/assets/` by replaying the documented CLI commands, so they
  can no longer silently drift from real output.
- Expanded DST and edge-case regression tests, including spring-forward and
  fall-back coverage for table construction and hour selection.

### Changed

- The PyPI classifier moves from `Development Status :: 4 - Beta` to
  `Development Status :: 5 - Production/Stable`. The CLI surface documented
  in the README is now considered stable; flags will not be renamed or
  removed again without a major version bump.
- **Breaking:** `--list`, `--search` and timezone arguments are now mutually
  exclusive. Combining them used to let the dispatch order silently pick a
  winner — `--list` beat `--search`, which beat a comparison — and still exit
  `0`. Combining them is now an argparse error with exit code `2`.
- **Breaking:** a bare `--search` with no word is now an argparse error with
  exit code `2`. It used to print the help text and exit `0`, which reads
  like success.
- **Breaking:** error output moves from stdout to stderr. An unknown timezone
  printed its message, and its table of closest matches, to stdout, so a
  redirected or piped run captured the error as if it were results. Errors
  now go through Rich on stderr and always exit `1`.
- `--hour` and `--list` report invalid values as ordinary argparse errors,
  e.g. `argument -H/--hour: Value for --hour must be between 00 and 23`. A
  non-numeric `--hour` now says so instead of reporting an
  `invalid _hour_value value`.

### Removed

- **Breaking:** `--single` / `-s` has been renamed to `--hour` / `-H`. The
  behavior of the flag is otherwise unchanged. If you script against this
  tool, replace `--single` with `--hour` and `-s` with `-H`; the old spelling
  is gone rather than deprecated, so it now fails with an argparse error
  instead of silently doing something else.

### Fixed

- `--version` no longer depends on `tzdata` being installed. The version was
  resolved while building the argument parser, so a missing distribution
  raised `PackageNotFoundError` before any argument could be parsed, taking
  the whole CLI down. Versions are now resolved only when `--version` is
  used, and an absent distribution reports `unknown`.
- **Breaking:** `--hour N` now selects the local **wall-clock** hour `N`
  instead of the instant `N` real hours after local midnight. The two are the
  same on ordinary 24-hour days and differ only across a DST transition,
  where the old arithmetic was simply wrong — on a spring-forward day every
  hour past the transition rendered an hour late (`--hour 14` showed
  `15:00`) and `--hour 23` could spill into the next date, while a fall-back
  day drifted the other way. Two consequences worth knowing:
  - A local hour that **happens twice** (fall back) now prints both instants,
    matching how the full-day table renders the repeat.
  - A local hour that **never happens** (spring forward) now exits non-zero
    with an explanation instead of printing an empty table.

### Notes

- Installation and Docker usage are unchanged: `pip install -U
  timezone-converter`, or `docker run --rm -t bledy/timezone-converter
  <timezone> [<timezone> ...]`.
- The comparison table already spanned the real local day (23, 24, or 25
  hours) across DST changes as of `v0.16.1`; `1.0.0` extends that same
  correctness to single-hour selection.
