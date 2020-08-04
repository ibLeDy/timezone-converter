# Timezone Converter

Compare a full day of your local timezone with a foreign one.

`$ python3 timezone_comparison.py tijuana`

<img src="https://git.io/JJKG6" alt="comparison between two timezones">

## Contents

- [Motivation](#motivation)
- [Getting started](#getting-started)
- [Available timezones](#available-timezones)
- [License](#license)

## Motivation

When working with people that are not in your local timezone, the available
resources are the usual webpages that only show _one_ hour at a time, which
is pretty inconvenient.

With this script you can quickly compare a full day of your timezone against
a foreign one.

## Getting started

Clone the repo

```bash
git clone https://github.com/ibLeDy/timezone-converter.git
cd timezone-converter
```

Create a new virtual enviroment and activate it

```bash
python3 -m virtualenv .venv
source .venv/bin/activate
```

Install the requirements

```bash
pip install -r requirements.txt
```

Run the script

```bash
python3 timezone_converter.py <timezone>
```

## Available timezones

You can use the argument `-l` or `--list` which will output all the available
timezones.

`$ python3 timezone_converter.py --list`

<center><img src="https://git.io/JJKGo" alt="available timezones"></center>

## License

This project is licensed under the terms of the [MIT] license.

[MIT]: https://choosealicense.com/licenses/mit/
