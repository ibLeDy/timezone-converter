import argparse
from datetime import datetime
from typing import List

from timezone_converter.comparison_view import ComparisonView
from timezone_converter.constants import VERSION
from timezone_converter.list_view import ListView


def _single_hour(argument: str) -> int:
    hour = int(argument)
    if hour not in range(24):
        raise argparse.ArgumentError(
            None,
            'Value for --single must be between 00 and 23',
        )
    return hour


def _single_letter(argument: List[str]) -> List[str]:
    if argument == 'all':
        return ['all']
    else:
        argument = list(argument)
        for letter in argument:
            if letter.isalpha() is False:
                raise argparse.ArgumentError(
                    'Value for --list must be single letters or None',
                )
        return argument


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='timezone-converter',
        description='Compare your local timezone with a foreign one',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'timezone',
        nargs='*',
        help='foreign timezone',
    )
    parser.add_argument(
        '-l',
        '--list',
        nargs='?',
        type=_single_letter,
        const='all',
        metavar='LETTER',
        help='show all available timezones or timezones beginning with specified letter groups',
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
    parser.add_argument(
        '-s',
        '--single',
        nargs='?',
        type=_single_hour,
        const=datetime.now().hour,
        metavar='HOUR',
        dest='hour',
        help='show a single hour',
    )
    return parser


def main() -> int:
    returncode = 0
    parser = build_parser()
    args = parser.parse_args()
    if args.list:
        returncode = ListView(args.list).print_columns()
    elif args.timezone:
        returncode = ComparisonView(
            args.timezone,
            args.zone,
            args.hour,
        ).print_table()
    else:
        parser.print_help()
    if returncode is None:
        returncode = 1
    return returncode


if __name__ == '__main__':
    exit(main())
