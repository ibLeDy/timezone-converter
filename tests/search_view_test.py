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


def test_search_includes_unambiguous_canonical_paths(capsys):
    SearchView('America/New_York').print_search_results()
    out = capsys.readouterr().out
    assert 'Found 1 timezone:' in out
    assert 'america/new_york' in out


def test_search_no_results(capsys):
    SearchView('zzzzzzzzzz').print_search_results()
    assert 'Found 0 timezones' in capsys.readouterr().out


def test_search_empty_string_finds_nothing(capsys):
    # Edge case: an empty search term (e.g. `--search ''`) must degrade
    # gracefully to zero matches instead of matching everything or raising.
    code = SearchView('').print_search_results()
    out = capsys.readouterr().out
    assert code == 0
    assert 'Found 0 timezones' in out


def test_search_single_character_finds_nothing(capsys):
    # Edge case: difflib's default similarity cutoff can't be cleared by a
    # single character against multi-character zone names, so a one-letter
    # filter (distinct from --list's single-letter grouping) should report
    # zero fuzzy matches rather than an arbitrary subset.
    code = SearchView('a').print_search_results()
    out = capsys.readouterr().out
    assert code == 0
    assert 'Found 0 timezones' in out
