import string

from timezone_converter.list_view import ListView


def test_list_groups_filtered_by_letter(capsys):
    code = ListView(['a']).print_columns()
    out = capsys.readouterr().out
    assert code == 0
    assert 'amsterdam' in out


def test_list_includes_ambiguous_canonical_paths(capsys):
    ListView(['a']).print_columns()
    out = capsys.readouterr().out
    assert 'asia/istanbul' in out


def test_list_all_letters(capsys):
    ListView(list(string.ascii_lowercase)).print_columns()
    assert 'utc' in capsys.readouterr().out


def test_list_letter_with_no_matches_prints_without_error(capsys):
    # Edge case: no available timezone name starts with "x", so the filtered
    # group is empty. This must render cleanly (no panel, no crash) rather
    # than assuming every requested letter has at least one match.
    code = ListView(['x']).print_columns()
    out = capsys.readouterr().out
    assert code == 0
    assert 'amsterdam' not in out
