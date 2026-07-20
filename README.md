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
timezone-converter tijuana --single 14
timezone-converter --search york
timezone-converter --list tbd
```

### Docker

```bash
docker run --rm -t bledy/timezone-converter <timezone> [<timezone> ...]
```

## Features

### Comparison between multiple timezones

Multiple timezones can be provided to get a side-by-side comparison.
Short timezone names such as `new_york` are supported, as are canonical
timezone paths such as `America/New_York`.

### Current hour highlighting

The row containing the current hour will be highlighted.

### Zone abbreviations

Using the `--zone` argument, each column header will include the timezone
abbreviation for that day, such as `PST` or `CEST`.

### Ordered columns

Using the `--order` argument, timezone columns will be sorted by their offset
difference from your local timezone.

### Output a single hour

Using the `--single` argument, you can output a single hour. If you don't
provide a value, the current hour will be displayed.

### Search for a timezone

Using the `--search` argument, you can fuzzy-search for available timezone
names.

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
