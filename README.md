<div align="center">
  <h1>Timezone Converter</h1>
  <h3>Compare a full day of your local timezone with foreign ones</h3>
  <br>
  <p>
    <a href="https://github.com/ibLeDy/timezone-converter/actions/workflows/integration.yml">
        <img alt="integration status" src="https://github.com/ibLeDy/timezone-converter/actions/workflows/integration.yml/badge.svg" />
    </a>
    <a href="https://github.com/ibLeDy/timezone-converter/actions/workflows/deployment.yml">
        <img alt="deployment status" src="https://github.com/ibLeDy/timezone-converter/actions/workflows/deployment.yml/badge.svg" />
    </a>
    <a href="https://results.pre-commit.ci/latest/github/ibLeDy/timezone-converter/main">
        <img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/ibLeDy/timezone-converter/main.svg" />
    </a>
    <a href="https://pypi.org/project/timezone-converter/">
        <img alt="python version" src="https://img.shields.io/pypi/pyversions/timezone-converter" />
    </a>
    <a href="https://pypi.org/project/timezone-converter/">
        <img alt="latest release" src="https://img.shields.io/pypi/v/timezone-converter?color=blue" />
    </a>
    <a href="https://github.com/psf/black">
        <img alt="code style" src="https://img.shields.io/badge/code%20style-black-000000.svg" />
    </a>
  </p>
</div>

<div align="center">
  <table>
    <tr>
      <th style="text-align: center;"><code>$ timezone-converter tijuana --zone</code></th>
      <th style="text-align: center;"><code>$ timezone-converter tijuana new_york</code></th>
    </tr>
    <tr>
      <td><img alt="comparison between two timezones with zone info" src="https://raw.githubusercontent.com/ibLeDy/timezone-converter/main/.github/assets/tijuana_zone.svg" /></td>
      <td><img alt="comparison between three timezones" src="https://raw.githubusercontent.com/ibLeDy/timezone-converter/main/.github/assets/tijuana_new_york.svg" /></td>
    </tr>
  </table>
</div>

---

## Motivation

When working with people that are not in your local timezone, the available
resources are the usual webpages that only show _one_ hour at a time, which
is pretty inconvenient.

With this package you can quickly compare a full day of your timezone against
foreign ones.

## Installation

```bash
pip install -U timezone-converter
```

## Usage

```bash
timezone-converter <timezone> [<timezone> ...]
```

The short alias `tzconv` also works, if you prefer less typing.

Useful flags:

```bash
timezone-converter tijuana new_york --zone
timezone-converter tijuana new_york --order
timezone-converter tijuana --hour 14
timezone-converter tijuana --date 2026-03-08
timezone-converter tijuana --local madrid
timezone-converter tijuana --format json
timezone-converter tijuana --difference
timezone-converter --search york
timezone-converter --list tbd
timezone-converter --version
```

`--list`, `--search`, and comparing timezones are three separate modes, so
only one of them can be used at a time. The flags that modify a comparison
(`--zone`, `--hour`, `--date`, `--local`, `--order`, `--difference`) need at
least one timezone: on their own they are an error, and next to `--list` or
`--search` they are ignored with a warning.

### Docker

```bash
docker run --rm -t -e TZ=Europe/Madrid bledy/timezone-converter <timezone> [<timezone> ...]
```

A container has no timezone of its own, so without `-e TZ` (or `--local`) the
`LOCAL` column is UTC. See
[Override your local timezone](#override-your-local-timezone) below.

## Features

### Comparison between multiple timezones

Multiple timezones can be provided to get a side-by-side comparison.
Short timezone names such as `new_york` are supported, as are canonical
timezone paths such as `America/New_York`.

A few short names are shared by more than one zone, such as `istanbul`,
which is both `Asia/Istanbul` and `Europe/Istanbul`. One of them is picked,
and a warning on stderr names the alternatives so you can give a full path
instead. The warning never touches the table itself, so piping the output
stays safe.

### Current hour highlighting

The row containing the current hour will be highlighted.

### Zone abbreviations

Using the `--zone` argument, each column header will include the timezone
abbreviation for that day, such as `PST` or `CEST`.

### Ordered columns

Using the `--order` argument, timezone columns will be sorted by their offset
difference from your local timezone.

### Difference in hours

Using the `--difference` argument, each column header will include the signed
difference in hours from your local timezone, such as `+9.5h` or `-5h`. When
combined with `--zone`, the difference is appended after the zone
abbreviation, e.g. `AMERICA/TIJUANA (PST) -8h`.

### Output a single hour

Using the `--hour` argument, you can output a single hour. If you don't
provide a value, the current hour will be displayed, as read in whichever
timezone counts as local (see `--local` and `TZ` below).

The value is a local wall-clock hour, so on the days your clocks change it
still refers to the hour you actually see on the clock. When your clocks fall
back, the repeated hour happens twice and both instants are shown. When they
spring forward, the skipped hour never happens, and asking for it is an error.

### Compare another day

Using the `--date` argument, you can compare a different local calendar day
instead of today, given as `YYYY-MM-DD`. The day is built from that date's
own timezone rules, so a day on which your clocks change still shows its
real 23 or 25 hours rather than today's offset applied to another date.

### Override your local timezone

Using the `--local` argument, you can pick which timezone the `LOCAL` column
represents, instead of the one your machine is set to. It accepts the same
names as any other timezone argument.

This matters when the machine's clock is not the one you care about, such as
inside a Docker container, where the host is usually set to UTC. Everything
follows the override: which day is "today", where midnight falls, which hour
`--hour` selects, and what `--difference` measures from.

Without `--local`, the `TZ` environment variable is honored the same way, which
is the usual way to give a container, a CI runner, or a Windows shell a local
timezone:

```bash
TZ=Europe/Madrid timezone-converter new_york
```

`TZ` is read with the same timezone database the rest of the tool uses, so an
IANA name such as `Europe/Madrid` resolves identically on every platform, and
on minimal container images that ship no system timezone data. If `TZ` is
unset, or holds something that is not an IANA name (such as a POSIX rule
string like `CET-1CEST,M3.5.0,M10.5.0/3`), your machine's timezone is used.
When both are set, `--local` wins.

### Machine-readable output

Using `--format json`, a comparison is printed as JSON instead of a table.
The table remains the default. It only applies to a comparison: with
`--list`, `--search`, or no timezones at all, it is an error rather than
being silently ignored, so a script never mistakes other output for JSON.

Times are ISO-8601 with their UTC offset, rather than the table's display
format, so the two instants of a repeated fall-back hour stay distinct. Each
column reports its resolved zone, its abbreviation for the day, and its
signed hour difference from local, and each row says whether it is the
current hour.

```json
{
  "date": "2026-06-01",
  "columns": [
    {
      "label": "LOCAL",
      "zone": "America/New_York",
      "abbreviation": "EDT",
      "difference_hours": 0.0
    },
    {
      "label": "ASIA/TOKYO",
      "zone": "Asia/Tokyo",
      "abbreviation": "JST",
      "difference_hours": 13.0
    }
  ],
  "rows": [
    {
      "current": false,
      "times": ["2026-06-01T00:00:00-04:00", "2026-06-01T13:00:00+09:00"]
    }
  ]
}
```

The `zone` of the `LOCAL` column is `null` unless you set `--local` or `TZ`,
because your machine's timezone is read as a plain UTC offset rather than a
named zone.

### Search for a timezone

Using the `--search` argument, you can fuzzy-search for available timezone
names.

### Version information

Using the `--version` argument, you can see the installed package version
along with the version of the `tzdata` database it is resolving timezones
against, e.g. `timezone-converter X.Y.Z (tzdata 2026.4)`.

### List of available timezones

Using the `--list` argument, you can see a pretty list of available timezones,
by groups, and sorted alphabetically.
You can optionally provide letters to filter the groups that are shown.

`$ timezone-converter --list`

![list of available timezones](https://raw.githubusercontent.com/ibLeDy/timezone-converter/main/.github/assets/list.svg)

## License

This project is licensed under the terms of the
[MIT](https://choosealicense.com/licenses/mit/) license.

<div align="right">
  <b><a href="#timezone-converter">↥ back to top</a></b>
</div>
