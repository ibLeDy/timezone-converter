import argparse

from timezone_converter.classes import TimezonesComparison
from timezone_converter.classes import TimezonesList
from timezone_converter.constants import VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='timezone-converter',
        description='Compare your local timezone with a foreign one',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'timezone',
        nargs='?',
        help='foreign timezone',
    )
    parser.add_argument(
        '-l',
        '--list',
        action='store_true',
        help='show all available timezones',
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}',
        help='show program\'s version number and exit',
    )
    parser.add_argument(
        '-z',
        '--zone',
        action='store_true',
        help='show corresponding zone name in each column',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.list:
        TimezonesList().print_columns()
    elif args.timezone is not None:
        TimezonesComparison(args.timezone, args.zone).print_table()
    else:
        parser.print_help()
