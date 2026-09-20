# Security policy

## Supported versions

Only the latest released version is supported. Fixes are published as a new
release rather than backported.

## Reporting a vulnerability

Please report security issues privately, through GitHub's
[private vulnerability reporting](https://github.com/ibLeDy/timezone-converter/security/advisories/new),
rather than by opening a public issue.

Useful things to include:

- what you did, ideally as a command line that reproduces it;
- what happened, and what you expected instead;
- the output of `timezone-converter --version`, which reports both the
  package version and the `tzdata` version in use;
- your operating system and Python version.

This is a small project maintained in spare time, so expect a first reply
within a couple of weeks. You will be credited in the advisory and the
release notes unless you would rather not be.

## Scope

This is an offline command-line tool. It reads its timezone data from
`zoneinfo` and the `tzdata` package and makes no network requests, so the
realistic surface is limited to how command-line input is handled and to the
dependencies listed in `pyproject.toml`.

Timezone data itself going stale is not a vulnerability: update the `tzdata`
package to pick up new rules.
