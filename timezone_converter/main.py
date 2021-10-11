import argparse
import string
from datetime import datetime
from typing import List
from typing import Optional

from timezone_converter.comparison_view import ComparisonView
from timezone_converter.constants import VERSION
from timezone_converter.list_view import ListView
from timezone_converter.search_view import SearchView


def _single_hour(argument: str) -> int:
    hour = int(argument)
    if hour not in range(24):
        raise argparse.ArgumentError(
            None,
            'Value for --single must be between 00 and 23',
        )
    return hour


def _list_letter(argument: str) -> List[str]:
    argument_set = set(argument)
    if any(not arg.isalpha() for arg in argument_set):
        raise argparse.ArgumentError(
            None,
            'Values for --list cannot contain numbers',
        )
    return sorted(argument_set)


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
        type=_list_letter,
        const=list(string.ascii_lowercase),
        metavar='LETTER',
        help='show all timezones or only those that start with specific letters',
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
    parser.add_argument(
        '-S',
        '--search',
        nargs='?',
        metavar='WORD',
        help='fuzzy search for a timezone',
    )
    parser.add_argument(
        '-o',
        '--order',
        action='store_true',
        help='show timezones in order of difference',
    )

    return parser


def main() -> int:
    returncode: Optional[int] = 0
    parser = build_parser()
    args = parser.parse_args()
    if args.list:
        returncode = ListView(args.list).print_columns()
    elif args.search:
        returncode = SearchView(args.search).print_search_results()
    elif args.timezone:
        returncode = ComparisonView(
            args.timezone,
            args.zone,
            args.hour,
            args.order,
        ).print_table()
    else:
        parser.print_help()

    if returncode is None:
        returncode = 1

    return returncode


if __name__ == '__main__':
    exit(main())
