# PR 3: CLI robustness (version, modes, exits)

> **For agentic workers:** TDD for each behavioral change. Checkbox
> tracking. Preserve view exit-code contracts (0 success, nonzero fail).

**Status:** Proposed
**Goal:** Make parser construction safe without installed `tzdata`
metadata side effects; make mode selection explicit; unify unknown-zone
errors; use idiomatic argparse type errors.
**Architecture:** Keep `main.main()` as dispatcher. Unknown zones return
exit codes from comparison path instead of mixed `SystemExit` strings
where practical; keep process exit nonzero.
**Tech stack:** argparse, importlib.metadata, Rich (stderr policy).

## Global constraints

See roadmap. Coordinated CLI changes: parser + tests + README (if UX
text changes) + tox as needed. Python 3.9 typing style.

## Design decisions (locked for this plan)

1. **`tzdata` version:** Resolve only for the version action string;
   if `PackageNotFoundError`, show `tzdata unknown` (or `tzdata (not installed as package)`). Parser construction must not raise.
2. **Mode exclusivity:** Exactly one of: list mode, search mode,
   comparison mode (one or more timezones), or help. If more than one
   of `{list is not None, search is not None, timezone non-empty}` is
   active, print a short error to stderr and return `2` (argparse-like).
3. **Bare `--search`:** Change `--search` to `nargs=1` **or** keep
   `nargs='?'` but treat `const` specially. **Chosen:** require a word:
   use `nargs=None` default (single required value when flag present):

   ```python
   parser.add_argument('-S', '--search', type=str.lower, metavar='WORD', ...)
   ```

   Then bare `--search` is argparse error (exit 2). Empty string still
   possible as `--search ''` — keep SearchView empty behavior.
4. **Unknown timezone:** Stop using `SystemExit(error_msg)`. Instead:
   - print error (and suggestions table) via a single helper that writes
     with Rich Console on **stderr** (`Console(stderr=True)`), then
     `raise SystemExit(1)` **or** return `1` from constructor path.
   - **Chosen approach:** change `_get_timezone_name` to return
     `Optional[str]` and have `__init__` collect failures…
     **Simpler chosen approach:** introduce
     `Helper._print_error_with_rich(obj)` using `Console(stderr=True)`,
     always `raise SystemExit(1)` after printing (never
     `SystemExit(str)`). Tests assert returncode 1 and message location.
5. **Keep** `returncode is None → 1` safety net and existing test.
6. **`ArgumentTypeError`** for `_hour_value` and `_list_letter`.

## File map

| File | Change |
|------|--------|
| `timezone_converter/main.py` | version helper, mode check, search nargs, ArgumentTypeError |
| `timezone_converter/helper.py` | optional `_print_error_with_rich` |
| `timezone_converter/comparison_view.py` | unified SystemExit(1) + stderr print |
| `tests/main_test.py` | version without tzdata, modes, bare search, type errors |
| `tests/comparison_view_test.py` | exit code / stderr for unknown zones |
| `README.md` | note that flags are exclusive if user-facing |

---

### Task 1: ArgumentTypeError converters

**Files:**
- Modify: `timezone_converter/main.py`
- Modify: `tests/main_test.py`

- [ ] **Step 1: Update tests** for invalid hour/list to still raise
  (argparse wraps type errors). Existing tests use
  `pytest.raises(argparse.ArgumentError)` when calling converters
  directly — change direct converter tests to:

```python
def test_hour_value_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        _hour_value('24')


def test_list_letter_rejects_digits():
    with pytest.raises(argparse.ArgumentTypeError):
        _list_letter('a1')
```

- [ ] **Step 2: Implement converters:**

```python
def _hour_value(argument: str) -> int:
    try:
        hour = int(argument)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'invalid hour value: {argument!r}',
        ) from None
    if hour not in range(24):
        raise argparse.ArgumentTypeError(
            'Value for --hour must be between 00 and 23',
        )
    return hour


def _list_letter(argument: str) -> List[str]:
    argument_set = set(argument.lower())
    if any(not arg.isalpha() for arg in argument_set):
        raise argparse.ArgumentTypeError(
            'Values for --list cannot contain numbers',
        )
    return sorted(argument_set)
```

- [ ] **Step 3: Run targeted tests; commit**

```bash
pytest tests/main_test.py -k 'hour_value or list_letter' -v
git add timezone_converter/main.py tests/main_test.py
git commit -m "fix: use ArgumentTypeError in CLI type converters"
```

---

### Task 2: Safe version string (lazy tzdata)

**Files:**
- Modify: `timezone_converter/main.py`
- Modify: `tests/main_test.py`

- [ ] **Step 1: Failing test** — parser builds even if tzdata metadata missing:

```python
def test_build_parser_without_tzdata_package(monkeypatch):
    def _boom(_name):
        raise importlib.metadata.PackageNotFoundError('tzdata')

    monkeypatch.setattr(
        'timezone_converter.main.importlib.metadata.version',
        _boom,
    )
    # VERSION lookup also uses metadata — only patch the call site helper.
    # Prefer testing the helper directly:
```

Better structure — add helper and test it:

```python
# main.py
def _tzdata_version_label() -> str:
    try:
        return importlib.metadata.version('tzdata')
    except importlib.metadata.PackageNotFoundError:
        return 'unknown'


# In build_parser:
# version=f'%(prog)s {VERSION} (tzdata {_tzdata_version_label()})',
# MUST NOT call version('tzdata') at import of build_parser beyond this helper.
```

Note: `action='version'` evaluates the version string when the action
runs if we pass a string — still computed at `build_parser()` time if
we format immediately. **Use a custom version action or format at
build time via the safe helper** (helper must not raise):

```python
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=f'%(prog)s {VERSION} (tzdata {_tzdata_version_label()})',
        help="show program's version number and exit",
    )
```

Test:

```python
import importlib.metadata

def test_tzdata_version_label_unknown(monkeypatch):
    def _boom(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, 'version', _boom)
    from timezone_converter.main import _tzdata_version_label
    assert _tzdata_version_label() == 'unknown'


def test_build_parser_does_not_raise_without_tzdata(monkeypatch):
    monkeypatch.setattr(
        'timezone_converter.main._tzdata_version_label',
        lambda: 'unknown',
    )
    args = build_parser().parse_args(['tijuana'])
    assert args.timezone == ['tijuana']
```

- [ ] **Step 2: Implement helper; remove bare
  `importlib.metadata.version('tzdata')` without try/except.**

- [ ] **Step 3: Keep existing test
  `test_build_parser_version_includes_tzdata_version`** — still expects
  `tzdata \d` when package present.

- [ ] **Step 4: Commit**

```bash
git commit -am "fix: tolerate missing tzdata distribution in --version"
```

---

### Task 3: Require search word; mode exclusivity

**Files:**
- Modify: `timezone_converter/main.py`
- Modify: `tests/main_test.py`
- Modify: `README.md` (brief note under Usage if helpful)

- [ ] **Step 1: Tests**

```python
def test_search_requires_word(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(['--search'])
    assert exc.value.code == 2


def test_main_rejects_list_and_timezone(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--list', 'a'])
    assert main() == 2
    err = capsys.readouterr().err
    assert 'not combine' in err.lower() or 'exclusive' in err.lower()


def test_main_rejects_search_and_timezone(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['tz', 'tijuana', '--search', 'york'])
    assert main() == 2
```

- [ ] **Step 2: Change `--search` definition** to require WORD:

```python
    parser.add_argument(
        '-S',
        '--search',
        type=str.lower,
        metavar='WORD',
        help='fuzzy search for a timezone',
    )
```

- [ ] **Step 3: Dispatch with exclusivity**

Prefer `return 2` (testable via `main()`) over `parser.exit()`:

```python
def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    modes = [
        args.list is not None,
        args.search is not None,
        bool(args.timezone),
    ]
    if sum(modes) > 1:
        sys.stderr.write(
            'error: --list, --search, and timezone arguments '
            'are mutually exclusive\n',
        )
        return 2

    returncode: Optional[int] = 0
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
        ).print_table()
    else:
        parser.print_help()

    if returncode is None:
        returncode = 1
    return returncode
```

Add `import sys` at the top of `main.py`.

**Important:** `--list` uses `nargs='?'` with `const=all letters`. When
the flag is absent, `args.list is None`. When present without value,
`args.list` is the full alphabet. Current code used `if args.list:`
which treats empty list as false — exclusivity must use
`is not None` for list/search.

Empty list after filter is still a valid list mode (print nothing).
Existing `ListView(['x'])` tests remain valid.

Update any tests that assumed `if args.list:` truthiness if needed.

- [ ] **Step 4: README** — under Useful flags, one line:

```markdown
`--list`, `--search`, and timezone arguments are mutually exclusive.
```

- [ ] **Step 5: Full tests + commit**

```bash
coverage run -m pytest && coverage report
git commit -am "fix: exclusive CLI modes and required --search WORD"
```

---

### Task 4: Unified unknown-timezone errors on stderr

**Files:**
- Modify: `timezone_converter/helper.py`
- Modify: `timezone_converter/comparison_view.py`
- Modify: `tests/comparison_view_test.py`

- [ ] **Step 1: Add helper**

```python
# helper.py
@staticmethod
def _print_error_with_rich(obj: Union[str, Columns, Table]) -> None:
    Console(stderr=True).print(obj)
```

- [ ] **Step 2: Change `_get_timezone_name`**

```python
    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.resolve_timezone(timezone)
        if timezone_name is None:
            error_msg = f'error: {timezone!r} is not an available timezone'
            possible_matches: List[str] = get_close_matches(
                timezone.lower(),
                self.searchable_timezones,
                n=5,
            )
            self._print_error_with_rich(error_msg)
            if possible_matches:
                table = Table()
                table.add_column('Closest matches')
                for match in possible_matches:
                    table.add_row(match)
                self._print_error_with_rich(table)
            raise SystemExit(1)
        return timezone_name
```

- [ ] **Step 3: Tests** (subprocess or capsys with stderr):

```python
def test_unknown_timezone_exits_one_with_message(capsys):
    with pytest.raises(SystemExit) as exc:
        _make_view(['zzzzzzzzzz'])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert 'zzzzzzzzzz' in captured.err
    assert captured.out == ''


def test_unknown_timezone_suggestions_on_stderr(capsys):
    with pytest.raises(SystemExit) as exc:
        _make_view(['new_yrk'])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert 'new_york' in err
```

- [ ] **Step 4: Commit**

```bash
git commit -am "fix: print unknown timezone errors on stderr with exit 1"
```

---

### Task 5: Verification and PR

- [ ] **Step 1:**

```bash
coverage run -m pytest && coverage report
pre-commit run --all-files
timezone-converter --version
timezone-converter --search   # expect usage error
timezone-converter tijuana --list a  # expect exclusive error
```

- [ ] **Step 2: Open PR**
  `fix: harden CLI parsing, mode exclusivity, and error output`
  Label as mild behavior change (exclusive modes, bare `--search`).

## Behavior change summary (for PR body)

- Bare `--search` now errors (exit 2) instead of printing help.
- Combining `--list`/`--search`/timezones errors (exit 2) instead of silent precedence.
- Unknown zone messages go to stderr; always exit code 1.
- Missing `tzdata` package no longer crashes parser construction.

## Self-review checklist

- [x] All PR 3 audit items covered.
- [x] `--list is not None` vs truthiness called out.
- [x] Tests specified for exclusivity and stderr.
