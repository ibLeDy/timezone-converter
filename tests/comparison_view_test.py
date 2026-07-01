from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo

import pytest

from timezone_converter.comparison_view import ComparisonView


def _make_view(timezones=('new_york',), zone=False, hour=None, order=False):
    return ComparisonView(list(timezones), zone, hour, order)


def test_resolves_valid_timezone_to_canonical_zone():
    view = _make_view(['new_york'])
    assert view.zones[0] is None
    assert str(view.zones[1]) == 'America/New_York'


def test_unknown_timezone_with_suggestions_exits():
    with pytest.raises(SystemExit):
        _make_view(['new_yrk'])


def test_unknown_timezone_without_suggestions_exits():
    with pytest.raises(SystemExit):
        _make_view(['zzzzzzzzzz'])


def test_base_instant_is_local_midnight_today(monkeypatch):
    fixed = datetime(2026, 3, 8, 15, 30)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(
        'timezone_converter.comparison_view.datetime',
        _FixedDateTime,
    )
    view = _make_view(['new_york'])
    base = view.base_instant
    assert (base.year, base.month, base.day) == (2026, 3, 8)
    assert (base.hour, base.minute) == (0, 0)
    assert base.tzinfo is not None


def test_order_sorts_by_true_offset_not_hhmm_digits(monkeypatch):
    # Regression: --order previously sorted by int(strftime('%z')), turning
    # +0530 into 530, so offset distances were measured on HHMM digits.
    view = _make_view(['gmt+12', 'calcutta'])
    view.base_instant = datetime(2026, 1, 15, tzinfo=datetime_timezone.utc)
    view.zones = [
        None,
        ZoneInfo('Etc/GMT+12'),
        ZoneInfo('Asia/Calcutta'),
    ]

    # Pin the local reference to -0330 (St John's) so the result is
    # independent of the machine timezone; foreign offsets stay real.
    real_offset = ComparisonView._offset

    def fake_offset(self, zone):
        if zone is None:
            return timedelta(hours=-3, minutes=-30)
        return real_offset(self, zone)

    monkeypatch.setattr(ComparisonView, '_offset', fake_offset)

    view._sort_timezone_display()
    # By true minutes Etc/GMT+12 (510) is closer to -0330 than
    # Asia/Calcutta (540); the buggy HHMM math reported the opposite.
    assert [None if z is None else str(z) for z in view.zones] == [
        None,
        'Etc/GMT+12',
        'Asia/Calcutta',
    ]


def test_order_via_constructor():
    view = _make_view(['new_york'], order=True)
    assert view.zones[0] is None


def test_dst_transition_is_normalized_across_the_day():
    # Regression: rows were built as midnight + timedelta on a fixed-offset
    # datetime, freezing the offset, so the spring-forward hour was wrong.
    view = _make_view(['new_york'])
    view.base_instant = datetime(
        2026,
        3,
        8,
        tzinfo=ZoneInfo('America/New_York'),
    )  # DST starts 02:00 -> 03:00
    view.zones = [None, ZoneInfo('America/New_York')]
    cells = list(view._build_table().columns[1]._cells)
    assert cells[1] == '2026-03-08 01:00'
    assert cells[2] == '2026-03-08 03:00'  # 02:00 does not exist
    assert '2026-03-08 02:00' not in cells


def test_headers_without_zone():
    view = _make_view(['new_york'])
    view.zones = [None, ZoneInfo('America/New_York')]
    assert view._get_headers() == ['LOCAL', 'AMERICA/NEW_YORK']


def test_headers_with_zone_include_abbreviation():
    view = _make_view(['new_york'], zone=True)
    view.base_instant = datetime(
        2026,
        3,
        8,
        tzinfo=ZoneInfo('America/New_York'),
    )
    view.zones = [None, ZoneInfo('America/New_York')]
    headers = view._get_headers()
    assert headers[0].startswith('LOCAL (')
    assert headers[1] == 'AMERICA/NEW_YORK (EST)'


def test_single_hour_builds_one_row():
    view = _make_view(['new_york'], hour=9)
    assert len(view._build_table().rows) == 1


def test_current_hour_row_is_highlighted():
    view = _make_view(['new_york'])
    styles = [row.style for row in view._build_table().rows]
    assert styles.count('blue') == 1


def test_print_table_returns_zero():
    assert _make_view(['new_york'], hour=9).print_table() == 0
