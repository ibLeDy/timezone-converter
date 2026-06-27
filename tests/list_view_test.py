import string

from timezone_converter.list_view import ListView


def test_list_groups_filtered_by_letter(capsys):
    code = ListView(['a']).print_columns()
    out = capsys.readouterr().out
    assert code == 0
    assert 'amsterdam' in out


def test_list_all_letters(capsys):
    ListView(list(string.ascii_lowercase)).print_columns()
    assert 'utc' in capsys.readouterr().out
