from timezone_converter.search_view import SearchView


def test_search_returns_close_matches(capsys):
    code = SearchView('new_yrk').print_search_results()
    out = capsys.readouterr().out
    assert code == 0
    assert 'new_york' in out


def test_search_exact_match_short_circuits(capsys):
    SearchView('new_york').print_search_results()
    out = capsys.readouterr().out
    assert 'Found 1 timezone:' in out
    assert 'new_york' in out


def test_search_is_case_insensitive(capsys):
    SearchView('York').print_search_results()
    assert 'new_york' in capsys.readouterr().out


def test_search_includes_ambiguous_canonical_paths(capsys):
    SearchView('Asia/Istanbul').print_search_results()
    assert 'asia/istanbul' in capsys.readouterr().out


def test_search_no_results(capsys):
    SearchView('zzzzzzzzzz').print_search_results()
    assert 'Found 0 timezones' in capsys.readouterr().out
