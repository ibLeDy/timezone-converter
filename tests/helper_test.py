from zoneinfo import available_timezones

from timezone_converter.helper import Helper


def test_translations_map_segment_to_canonical():
    assert Helper.timezone_translations['new_york'] == 'America/New_York'


def test_available_timezones_include_short_names_and_shadowed_paths():
    assert 'new_york' in Helper.available_timezones
    assert 'asia/istanbul' in Helper.available_timezones
    assert 'europe/istanbul' in Helper.available_timezones


def test_searchable_timezones_include_all_canonical_paths():
    for tz in available_timezones():
        assert tz.lower() in Helper.searchable_timezones


def test_print_with_rich_outputs(capsys):
    Helper._print_with_rich('hello world')
    assert 'hello world' in capsys.readouterr().out


def test_short_name_resolves():
    assert Helper.resolve_timezone('new_york') == 'America/New_York'


def test_resolution_is_case_insensitive():
    assert Helper.resolve_timezone('EUROPE/ISTANBUL') == 'Europe/Istanbul'


def test_unknown_timezone_resolves_to_none():
    assert Helper.resolve_timezone('zzzzzzzzzz') is None


def test_every_timezone_is_reachable():
    # Several zones share a last path segment (e.g. Asia/Istanbul vs
    # Europe/Istanbul); none may be silently unreachable.
    for tz in available_timezones():
        assert Helper.resolve_timezone(tz) == tz


def test_ambiguous_short_name_lists_every_candidate():
    assert Helper.ambiguous_alternatives('istanbul') == [
        'Asia/Istanbul',
        'Europe/Istanbul',
    ]


def test_ambiguous_alternatives_is_case_insensitive():
    assert Helper.ambiguous_alternatives('ISTANBUL') == [
        'Asia/Istanbul',
        'Europe/Istanbul',
    ]


def test_unambiguous_short_name_has_no_alternatives():
    assert Helper.ambiguous_alternatives('new_york') == []


def test_a_full_path_is_never_ambiguous():
    # The user already said which one they meant.
    assert Helper.ambiguous_alternatives('Europe/Istanbul') == []
    assert Helper.ambiguous_alternatives('asia/istanbul') == []


def test_unknown_name_has_no_alternatives():
    assert Helper.ambiguous_alternatives('zzzzzzzzzz') == []


def test_a_short_name_that_is_itself_a_zone_is_not_ambiguous():
    # ``UTC`` and ``Jamaica`` are real top-level zones as well as the last
    # segment of others (``Etc/UTC``, ``America/Jamaica``). Asking for them
    # gets that exact zone, so there is nothing to warn about.
    assert Helper.ambiguous_alternatives('utc') == []
    assert Helper.resolve_timezone('utc') == 'UTC'
    assert Helper.ambiguous_alternatives('jamaica') == []
    assert Helper.resolve_timezone('jamaica') == 'Jamaica'


def test_every_alternative_resolves_to_itself():
    # The warning is only useful if the paths it suggests actually work.
    for name in Helper.ambiguous_alternatives('istanbul'):
        assert Helper.resolve_timezone(name) == name


def test_shadowed_zone_reachable_by_full_path():
    short = Helper.resolve_timezone('istanbul')
    assert short in ('Asia/Istanbul', 'Europe/Istanbul')
    assert Helper.resolve_timezone('asia/istanbul') == 'Asia/Istanbul'
    assert Helper.resolve_timezone('europe/istanbul') == 'Europe/Istanbul'
