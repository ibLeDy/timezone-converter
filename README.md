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
      <td><img alt="comparison between two timezones" src="https://git.io/JtaZj" /></td>
      <td><img alt="comparison between two timezones" src="https://git.io/JsJUv" /></td>
    </tr>
  </table>
</div>

---

## Table of Contents

- [Motivation](#motivation)
- [Installation](#installation)
- [Usage](#usage)
- [Available timezones](#available-timezones)
- [License](#license)

## Motivation

When working with people that are not in your local timezone, the available
resources are the usual webpages that only show _one_ hour at a time, which
is pretty inconvenient.

With this script you can quickly compare a full day of your timezone against
foreign ones.

## Installation

```bash
pip install -U timezone-converter
```

## Usage

```bash
timezone-converter <timezone> [<timezone> ...]
```

## Available timezones

`$ timezone-converter --list`

![list of available timezones](https://git.io/JJKGo)

## License

This project is licensed under the terms of the
[MIT](https://choosealicense.com/licenses/mit/) license.

<div align="right">
  <b><a href="#timezone-converter">↥ back to top</a></b>
</div>
