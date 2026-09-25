# Changelog

All notable user-facing changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases before `1.0.0` are not backfilled here; see the
[GitHub releases](https://github.com/ibLeDy/timezone-converter/releases) for
their notes.

## [Unreleased]

## [1.0.0] - 2026-09-25

First stable release. Everything below has been sitting on `main` since
`v0.16.1` without being published, so this is the release that actually ships
it.

**Upgrading from `0.16.1`:** 1.0.0 needs Python 3.10 or newer. If you script
against this tool, also read every entry marked **Breaking** below: one is
that Python 3.9 removal, two are about `--hour`, and the rest are cases where
the CLI used to succeed quietly and now reports an error, plus the move of
error output from stdout to stderr.

### Added

- `tzconv` as a short console-script alias for `timezone-converter`. Both
  entry points are installed and behave identically.
- `--difference` / `-d`, which appends each foreign column's signed hour
  offset from your local timezone to its header, such as `+9.5h` or `-5h`.
  Combined with `--zone` the difference follows the abbreviation, e.g.
  `AMERICA/TIJUANA (PST) -8h`. The `LOCAL` column is excluded, since its
  offset from itself is always zero.
- `--date YYYY-MM-DD` / `-D`, to compare a local calendar day other than
  today. The day is built from that date's own timezone rules, so a past or
  future DST transition day still shows its real 23 or 25 hours rather than
  today's offset applied to another date. Combines with `--hour`, which
  still means the wall-clock hour on the chosen day.
- `--local TIMEZONE` / `-L`, to pick which timezone the `LOCAL` column
  represents instead of the machine's own. Useful when the machine's clock is
  not the one that matters, such as inside a Docker container on a UTC host.
  The override decides what "today" means, where midnight falls, which hour is
  current for a bare `--hour`, which instant `--hour` selects and what
  `--difference` measures from. Unknown names fail exactly like any other
  timezone argument.
- `--format {table,json}` / `-f`, printing a comparison as JSON for other
  programs to read. The table stays the default. Times are ISO-8601 with
  their UTC offset rather than the table's display format, so the two
  instants of a repeated fall-back hour stay distinct; each column reports
  its resolved zone, abbreviation and signed hour difference from local, and
  each row says whether it is the current hour. It only applies to a
  comparison: with `--list`, `--search` or no timezones it is a usage error
  (exit code `2`), never output a script could mistake for JSON.
- A warning when a short timezone name is shared by more than one zone,
  such as `istanbul`, which is both `Asia/Istanbul` and `Europe/Istanbul`.
  Which one wins is an implementation detail of the lookup table, so the
  warning names the zone used and the alternatives to reach with a full
  path. It goes to stderr and the resolution is unchanged, so scripts and
  pipes are unaffected.
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
- **Breaking:** Python 3.9 is no longer supported; 1.0.0 requires Python 3.10
  or newer. 3.9 reached end of life in October 2025. On 3.9, `pip` keeps
  installing `0.16.1`, since it honors the package's `requires-python`.

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
- `TZ` now reliably sets the local timezone when `--local` is not given, so
  `docker run -e TZ=Europe/Madrid ...` gives the `LOCAL` column you asked for.
  It used to be read by the C library, which needs the operating system's
  timezone database: on images without it, such as slim containers, an IANA
  name was silently misread as a POSIX rule, producing a column labelled
  `Europe` at UTC+0, and on Windows it was not honored at all. `TZ` is now
  resolved with the bundled `tzdata`, identically on every platform. Values
  that are not IANA names, such as POSIX rule strings, still fall back to the
  machine's timezone, and `--local` wins when both are set.
- `--search` with no matches prints `Found 0 timezones` instead of ending the
  line with a dangling `: `.

### Notes

- Installation is unchanged on Python 3.10+: `pip install -U
  timezone-converter`. With Docker, pass your timezone so the `LOCAL` column
  is not UTC: `docker run --rm -t -e TZ=Europe/Madrid
  bledy/timezone-converter <timezone> [<timezone> ...]`. The image is now
  based on Debian trixie.
- The comparison table already spanned the real local day (23, 24, or 25
  hours) across DST changes as of `v0.16.1`; `1.0.0` extends that same
  correctness to single-hour selection.
