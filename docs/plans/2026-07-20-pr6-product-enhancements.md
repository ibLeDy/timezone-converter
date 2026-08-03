# PR 6: Product enhancements (optional track)

> **For agentic workers:** Implement only after PR 1–5 (or as
> separate feature PRs split further). Each feature below can be its
> **own PR** if preferred. Checkbox tracking. Coordinated CLI changes
> required per AGENTS.md.

**Status:** Proposed
**Goal:** Deliver audit “later / product” items: fixed date, local
override, machine-readable output, ambiguous short-name feedback.
**Architecture:** Extend `ComparisonView` construction and `main`
parser; keep DST-aware instant building. Prefer small flags over
subcommands.
**Tech stack:** argparse, zoneinfo, Rich (human), json module (machine).

## Global constraints

See roadmap. Each flag: parser + dispatch + view + tests + README + tox
smoke + AGENTS. Python 3.9 typing. 100% coverage.

## Features (implement in this order)

### Feature A — `--date YYYY-MM-DD`

**Semantics:** Set comparison local calendar day to the given date
instead of today. `base_instant` becomes local midnight on that date
(via `_to_local` / system or `--local` zone).

**Parser:**

```python
def _date_value(argument: str) -> datetime.date:
    try:
        return datetime.strptime(argument, '%Y-%m-%d').date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            'Value for --date must be YYYY-MM-DD',
        ) from exc

parser.add_argument(
    '--date',
    type=_date_value,
    metavar='YYYY-MM-DD',
    help='local calendar date to compare (default: today)',
)
```

**ComparisonView:** accept `Optional[date]`; if set, build
`base_instant` from that date at midnight in the local zone.

**Tests:** fixed date with monkeypatched local zone; DST date
2026-03-08 with `--hour 14` after PR 4.

**Tox smoke:** `timezone-converter tijuana --date 2026-01-15 --hour 12`

---

### Feature B — `--local TIMEZONE`

**Semantics:** Override the LOCAL column’s zone (and local midnight)
instead of the host system zone. Critical for Docker (`UTC` host).

**Implementation sketch:**

- Resolve name via `Helper.resolve_timezone`.
- Patch comparison to use `ZoneInfo(name)` wherever `_to_local` is used
  for “local”, **or** pass `local_zone: Optional[tzinfo]` into
  ComparisonView and replace `_to_local(instant)` with
  `instant.astimezone(local_zone)` when set.
- Prefer injecting local zone into ComparisonView over global
  monkeypatch in production code.

**Tests:** `--local utc` with foreign `new_york` yields stable headers
independent of host TZ.

**Tox smoke:** `timezone-converter new_york --local utc --hour 0`

---

### Feature C — `--format {table,json}` (default table)

**Semantics:**

- `table` — current Rich table (default).
- `json` — stdout JSON array of row objects:
  `{"local": "...", "America/New_York": "...", ...}` with ISO-like
  strings matching table cells (`%Y-%m-%d %H:%M`) **or** true ISO-8601
  offsets — **choose one and document**. Recommended: same strings as
  table for parity, plus a top-level `"headers"` list.

**Rules:**

- JSON mode should not use Rich color; print plain JSON to stdout.
- Errors still stderr + nonzero exit.
- Highlighting is table-only (omit from JSON).

**Tests:** parse JSON with `json.loads`; one-hour mode single element.

**Tox smoke:** `timezone-converter tijuana --hour 8 --format json`

---

### Feature D — Ambiguous short-name warning

**Semantics:** When the user passes a short segment that appears in
`_AMBIGUOUS_SEGMENTS` (e.g. `istanbul`), resolve as today (last-wins /
current `resolve_timezone` behavior) but print a **stderr** warning
listing canonical alternatives and the chosen zone:

```
warning: 'istanbul' is ambiguous; using Europe/Istanbul. Also available: Asia/Istanbul, Europe/Istanbul
```

Do not warn when user passes a full path.

**Tests:** capsys stderr for `istanbul`; no warning for
`Europe/Istanbul`.

**Optional stricter mode (out of scope unless requested):**
`--strict-ambiguous` exits 1.

---

## File map (all features)

| File | Role |
|------|------|
| `timezone_converter/main.py` | flags + dispatch |
| `timezone_converter/comparison_view.py` | date/local/format |
| `timezone_converter/helper.py` | ambiguous warning helper |
| `tests/comparison_view_test.py` | core behavior |
| `tests/main_test.py` | parser |
| `README.md` / `AGENTS.md` / tox in `pyproject.toml` | coordinated updates |
| `CHANGELOG.md` | Unreleased notes per feature |

## Suggested PR split

| PR | Contents |
|----|----------|
| 6a | `--date` |
| 6b | `--local` |
| 6c | `--format json` |
| 6d | ambiguous short-name warning |

Each gets its own branch: `grok/feat-date`, etc.

## Task template (repeat per feature)

- [ ] **Step 1:** Write failing parser + view tests.
- [ ] **Step 2:** Implement minimal code (3.9 typing, MyPy clean).
- [ ] **Step 3:** Update README feature section + examples.
- [ ] **Step 4:** Add tox smoke command(s).
- [ ] **Step 5:** `coverage run -m pytest && coverage report` → 100%.
- [ ] **Step 6:** `pre-commit run --all-files`.
- [ ] **Step 7:** Commit with Conventional Commit
  (`feat: add --date for fixed local calendar day`).
- [ ] **Step 8:** Open PR; mark ready when CI green.

## Versioning

- Features A–C → minor version bumps when released (can batch).
- Feature D → minor or patch; document under Changed/Fixed.

## Self-review checklist

- [x] All audit “product later” items represented.
- [x] Split guidance avoids one mega-PR.
- [x] DST and Docker local override called out.
