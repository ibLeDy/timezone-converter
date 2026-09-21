import argparse
import string
from datetime import date
from datetime import datetime
from typing import Any
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from timezone_converter.comparison_view import ComparisonView
from timezone_converter.constants import distribution_version
from timezone_converter.list_view import ListView
from timezone_converter.search_view import SearchView


def _hour_value(argument: str) -> int:
    # ``ArgumentTypeError`` is the exception argparse documents for ``type``
    # callables: it turns it into a ``prog: error: argument --hour: ...``
    # message and exit code 2, instead of the bare ``invalid _hour_value
    # value`` it produces for a leaked ``ValueError``.
    try:
        hour = int(argument)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'{argument !r} is not a whole number of hours',
        )
    if hour not in range(24):
        raise argparse.ArgumentTypeError(
            'Value for --hour must be between 00 and 23',
        )
    return hour


def _date_value(argument: str) -> date:
    try:
        return datetime.strptime(argument, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'{argument !r} is not a date in YYYY-MM-DD form',
        )


def _list_letter(argument: str) -> List[str]:
    argument_set = set(argument.lower())
    if any(not arg.isalpha() for arg in argument_set):
        raise argparse.ArgumentTypeError(
            'Values for --list cannot contain numbers',
        )
    return sorted(argument_set)


class _VersionAction(argparse.Action):
    """Print version information, resolving it only when asked for.

    Looking the versions up inside the action rather than while building
    the parser keeps distribution metadata off the path of every ordinary
    invocation, and means a missing distribution cannot break parsing.
    """

    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        help: Optional[str] = None,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=argparse.SUPPRESS,
            nargs=0,
            help=help,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        """Print the package and tzdata versions, then exit successfully."""
        package_version = distribution_version('timezone-converter')
        tzdata_version = distribution_version('tzdata')
        print(f'{parser.prog} {package_version} (tzdata {tzdata_version})')
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured with the ``timezone``, ``--list``, ``--version``,
        ``--zone``, ``--hour``, ``--search``, ``--date``, ``--order``, and
        ``--difference`` arguments.
    """
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
        action=_VersionAction,
        help='show program\'s version number and exit',
    )
    parser.add_argument(
        '-z',
        '--zone',
        action='store_true',
        help='show corresponding zone name in each column',
    )
    parser.add_argument(
        '-H',
        '--hour',
        nargs='?',
        type=_hour_value,
        const=datetime.now().hour,
        metavar='HOUR',
        dest='hour',
        help='show a single hour',
    )
    parser.add_argument(
        '-S',
        '--search',
        type=str.lower,
        metavar='WORD',
        help='fuzzy search for a timezone',
    )
    parser.add_argument(
        '-D',
        '--date',
        type=_date_value,
        metavar='YYYY-MM-DD',
        help='compare this local calendar day instead of today',
    )
    parser.add_argument(
        '-o',
        '--order',
        action='store_true',
        help='show timezones in order of difference',
    )
    parser.add_argument(
        '-d',
        '--difference',
        action='store_true',
        help='show difference in hours from your local timezone in each column',
    )

    return parser


def _validate_modes(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    # ``--list``, ``--search`` and a comparison are three different programs
    # sharing one entry point, and combining them used to let the dispatch
    # order silently pick a winner. A mutually exclusive argparse group
    # cannot express this, because the positional is variadic, so the check
    # lives here; ``parser.error`` still gives the usual usage-on-stderr and
    # exit code 2.
    modes = []
    if args.list is not None:
        modes.append('--list')
    if args.search is not None:
        modes.append('--search')
    if args.timezone:
        modes.append('timezone arguments')

    if len(modes) > 1:
        parser.error(f'{" and ".join(modes)} cannot be combined, pick one')


def main() -> int:
    """Parse command-line arguments and dispatch to the requested view.

    Returns
    -------
    int
        Process exit code suitable for ``sys.exit``.
    """
    returncode: Optional[int] = 0
    parser = build_parser()
    args = parser.parse_args()
    _validate_modes(parser, args)
    # ``is not None`` rather than truthiness: an empty value is still an
    # explicit request for that mode (``--list ''`` selects no letters), and
    # falling through to the help text would hide it.
    if args.list is not None:
        returncode = ListView(args.list).print_columns()
    elif args.search is not None:
        returncode = SearchView(args.search).print_search_results()
    elif args.timezone:
        returncode = ComparisonView(
            args.timezone,
            args.zone,
            args.hour,
            args.order,
            args.difference,
            args.date,
        ).print_table()
    else:
        parser.print_help()

    if returncode is None:
        returncode = 1

    return returncode


if __name__ == '__main__':
    # ``SystemExit`` rather than ``exit()``: the latter is installed by the
    # ``site`` module and is missing under ``python -S``.
    raise SystemExit(main())
