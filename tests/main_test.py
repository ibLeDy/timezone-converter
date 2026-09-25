import argparse
import re
from datetime import date
from importlib import metadata

import pytest

from timezone_converter import main as main_module
from timezone_converter.comparison_view import CURRENT_HOUR
from timezone_converter.main import _date_value
from timezone_converter.main import _hour_value
from timezone_converter.main import _list_letter
from timezone_converter.main import build_parser
from timezone_converter.main import main


def test_hour_value_valid():
    assert _hour_value('0') == 0
    assert _hour_value('23') == 23


def test_hour_value_invalid():
    # ArgumentTypeError, not ArgumentError: it is the exception argparse
    # documents for ``type`` callables, and the one it renders as a normal
    # ``argument -H/--hour: ...`` message.
    with pytest.raises(argparse.ArgumentTypeError):
        _hour_value('24')


def test_hour_value_rejects_non_numbers():
    with pytest.raises(argparse.ArgumentTypeError, match='whole number'):
        _hour_value('noon')


def test_date_value_parses_iso_dates():
    assert _date_value('2026-03-08') == date(2026, 3, 8)


@pytest.mark.parametrize('argument', ('08-03-2026', '2026-13-01', 'tomorrow', ''))
def test_date_value_rejects_anything_else(argument):
    with pytest.raises(argparse.ArgumentTypeError, match='YYYY-MM-DD'):
        _date_value(argument)


def test_invalid_date_exits_two_with_message_on_stderr(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(['tijuana', '--date', 'tomorrow'])
    assert exit_info.value.code == 2
    assert 'YYYY-MM-DD' in capsys.readouterr().err


def test_list_letter_normalizes():
    assert _list_letter('cba') == ['a', 'b', 'c']
    assert _list_letter('aab') == ['a', 'b']
    assert _list_letter('BA') == ['a', 'b']


def test_list_letter_rejects_digits():
    with pytest.raises(argparse.ArgumentTypeError):
        _list_letter('a1')


def test_invalid_hour_exits_two_with_message_on_stderr(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(['--hour', '24'])
    assert exit_info.value.code == 2
    assert 'between 00 and 23' in capsys.readouterr().err


def test_hour_without_a_value_defers_to_the_view():
    # The current hour depends on the local zone, which the parser does not
    # know yet, so it must not fill in the machine's hour itself.
    args = build_parser().parse_args(['new_york', '--hour'])
    assert args.hour == CURRENT_HOUR


def test_hour_rejects_the_current_hour_marker():
    # The marker must stay unreachable from the command line.
    with pytest.raises(argparse.ArgumentTypeError):
        _hour_value(str(CURRENT_HOUR))


def test_invalid_list_letter_exits_two_with_message_on_stderr(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(['--list', 'a1'])
    assert exit_info.value.code == 2
    assert 'cannot contain numbers' in capsys.readouterr().err


def test_build_parser_defaults():
    args = build_parser().parse_args(['tijuana'])
    assert args.timezone == ['tijuana']
    assert args.zone is False
    assert args.difference is False
    assert args.list is None


def test_build_parser_difference_flag():
    args = build_parser().parse_args(['tijuana', '--difference'])
    assert args.difference is True
    args = build_parser().parse_args(['tijuana', '-d'])
    assert args.difference is True


def test_build_parser_normalizes_search():
    args = build_parser().parse_args(['--search', 'York'])
    assert args.search == 'york'


def test_build_parser_version_includes_tzdata_version(capsys):
    with pytest.raises(SystemExit):
        build_parser().parse_args(['--version'])
    output = capsys.readouterr().out
    assert re.search(r'tzdata \d', output)


def test_build_parser_does_not_resolve_versions_until_asked(monkeypatch):
    # Distribution metadata is only needed to answer --version, so building
    # the parser must not touch it; a missing dist used to take the whole CLI
    # down at import time.
    def _explode(distribution):
        raise AssertionError(f'resolved {distribution} while building parser')

    monkeypatch.setattr(metadata, 'version', _explode)
    build_parser().parse_args(['tijuana'])


def test_version_reports_unknown_when_distribution_is_missing(capsys):
    def _missing(distribution):
        raise metadata.PackageNotFoundError(distribution)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(metadata, 'version', _missing)
        with pytest.raises(SystemExit) as exit_info:
            build_parser().parse_args(['--version'])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == (
        'timezone-converter unknown (tzdata unknown)'
    )


def test_search_requires_a_word(capsys):
    # A bare --search used to fall through to the help text with exit 0,
    # which reads like success.
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(['--search'])
    assert exit_info.value.code == 2
    assert 'expected one argument' in capsys.readouterr().err


def _patch_view(monkeypatch, name, method, returns=0):
    recorded = {}

    class _FakeView:
        def __init__(self, *args):
            recorded['args'] = args

        def _run(self):
            recorded['called'] = name
            return returns

    setattr(_FakeView, method, _FakeView._run)
    monkeypatch.setattr(main_module, name, _FakeView)
    return recorded


def test_main_dispatches_to_list_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', '--list', 'a'])
    recorded = _patch_view(monkeypatch, 'ListView', 'print_columns')
    assert main() == 0
    assert recorded['called'] == 'ListView'


def test_main_dispatches_to_search_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', '--search', 'york'])
    recorded = _patch_view(monkeypatch, 'SearchView', 'print_search_results')
    assert main() == 0
    assert recorded['called'] == 'SearchView'


def test_main_dispatches_to_comparison_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['called'] == 'ComparisonView'


# ComparisonView takes its arguments positionally, so name the positions
# rather than indexing from the end: a new trailing argument would otherwise
# silently retarget an existing assertion.
DATE_ARG = 5
LOCAL_ARG = 6
FORMAT_ARG = 7


def test_main_passes_the_date_to_the_comparison_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--date', '2026-03-08'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][DATE_ARG] == date(2026, 3, 8)


def test_main_passes_no_date_when_the_flag_is_absent(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][DATE_ARG] is None


def test_main_passes_the_local_override_to_the_comparison_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--local', 'new_york'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][LOCAL_ARG] == 'new_york'


def test_main_passes_no_local_override_when_the_flag_is_absent(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][LOCAL_ARG] is None


def test_main_passes_the_output_format_to_the_comparison_view(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--format', 'json'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][FORMAT_ARG] == 'json'


def test_format_defaults_to_table(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['args'][FORMAT_ARG] == 'table'


def test_unknown_format_exits_two(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(['tijuana', '--format', 'yaml'])
    assert exit_info.value.code == 2
    assert 'invalid choice' in capsys.readouterr().err


def test_main_prints_help_without_args(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['tz'])
    assert main() == 0
    assert 'usage' in capsys.readouterr().out


def test_empty_list_value_still_selects_list_mode(monkeypatch):
    # ``--list ''`` selects no letters, which is an empty list and therefore
    # falsy; dispatching on truthiness used to silently print help instead.
    monkeypatch.setattr('sys.argv', ['tz', '--list', ''])
    recorded = _patch_view(monkeypatch, 'ListView', 'print_columns')
    assert main() == 0
    assert recorded['called'] == 'ListView'
    assert recorded['args'] == ([],)


def test_empty_search_value_still_selects_search_mode(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', '--search', ''])
    recorded = _patch_view(monkeypatch, 'SearchView', 'print_search_results')
    assert main() == 0
    assert recorded['called'] == 'SearchView'


def test_main_returns_one_when_view_returns_none(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    _patch_view(monkeypatch, 'ComparisonView', 'print_table', returns=None)
    assert main() == 1


@pytest.mark.parametrize(
    'argv',
    (
        ['--list', 'a', '--search', 'york'],
        ['--list', 'a', 'tijuana'],
        ['--search', 'york', 'tijuana'],
        ['--list', 'a', '--search', 'york', 'tijuana'],
    ),
)
def test_combining_modes_exits_two(monkeypatch, capsys, argv):
    # The dispatch order used to pick a silent winner between the three modes.
    monkeypatch.setattr('sys.argv', ['tz', *argv])
    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code == 2
    assert 'cannot be combined' in capsys.readouterr().err


@pytest.mark.parametrize(
    'argv',
    (
        ['--format', 'json'],
        ['--list', 'tbd', '--format', 'json'],
        ['--search', 'york', '--format', 'json'],
    ),
)
def test_json_format_without_a_comparison_exits_two(monkeypatch, capsys, argv):
    # Regression: the flag was ignored, so these printed the help text or a
    # Rich panel on stdout and exited 0, although JSON had been asked for.
    monkeypatch.setattr('sys.argv', ['tz', *argv])
    with pytest.raises(SystemExit) as exit_info:
        main()
    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert '--format json only applies to a comparison' in captured.err
    assert captured.out == ''


def test_table_format_stays_accepted_without_a_comparison(monkeypatch):
    # ``table`` is the default, so spelling it out changes nothing anywhere.
    monkeypatch.setattr('sys.argv', ['tz', '--list', 'tbd', '--format', 'table'])
    recorded = _patch_view(monkeypatch, 'ListView', 'print_columns')
    assert main() == 0
    assert recorded['called'] == 'ListView'


def test_modifier_flags_are_not_treated_as_a_second_mode(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--zone', '--order'])
    recorded = _patch_view(monkeypatch, 'ComparisonView', 'print_table')
    assert main() == 0
    assert recorded['called'] == 'ComparisonView'
