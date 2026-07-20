import argparse
import re

import pytest

from timezone_converter import main as main_module
from timezone_converter.main import _hour_value
from timezone_converter.main import _list_letter
from timezone_converter.main import build_parser
from timezone_converter.main import main


def test_hour_value_valid():
    assert _hour_value('0') == 0
    assert _hour_value('23') == 23


def test_hour_value_invalid():
    with pytest.raises(argparse.ArgumentError):
        _hour_value('24')


def test_list_letter_normalizes():
    assert _list_letter('cba') == ['a', 'b', 'c']
    assert _list_letter('aab') == ['a', 'b']
    assert _list_letter('BA') == ['a', 'b']


def test_list_letter_rejects_digits():
    with pytest.raises(argparse.ArgumentError):
        _list_letter('a1')


def test_build_parser_defaults():
    args = build_parser().parse_args(['tijuana'])
    assert args.timezone == ['tijuana']
    assert args.zone is False
    assert args.list is None


def test_build_parser_normalizes_search():
    args = build_parser().parse_args(['--search', 'York'])
    assert args.search == 'york'


def test_build_parser_version_includes_tzdata_version(capsys):
    with pytest.raises(SystemExit):
        build_parser().parse_args(['--version'])
    output = capsys.readouterr().out
    assert re.search(r'tzdata \d', output)


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


def test_main_prints_help_without_args(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['tz'])
    assert main() == 0
    assert 'usage' in capsys.readouterr().out


def test_main_returns_one_when_view_returns_none(monkeypatch):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana'])
    _patch_view(monkeypatch, 'ComparisonView', 'print_table', returns=None)
    assert main() == 1
