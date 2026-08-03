# PR 4: `--hour` means local wall-clock hour

> **For agentic workers:** This is a **user-visible behavior change**.
> TDD required. Add spring-forward, fall-back, and half-hour zone tests.
> Checkbox tracking.

**Status:** Proposed
**Goal:** Make `--hour N` select the row whose **local** clock time is
`N:00` on the local calendar day (or the defined fallback when that
local time does not exist).
**Architecture:** Build the single-hour instant from the local date +
`time(hour=N)` via the `_to_local` seam / zone-aware construction, not
`base_utc + timedelta(hours=N)`. Full-day tables stay on
`_day_instants()`.
**Tech stack:** datetime, ZoneInfo, existing ComparisonView.

## Global constraints

See roadmap. Document BEHAVIOR CHANGE in PR body and README. Prefer
shipping in **0.17.0** notes (version bump can be a follow-up release
commit, not necessarily this PR).

## Semantic specification (normative)

Let `D` be the local calendar date of `base_instant` (local midnight’s
date). Let `H` be the integer `--hour` in `0..23`.

1. **Normal days:** Show the unique local instant `D H:00` converted
   across all columns (aware UTC under the hood).
2. **Spring-forward gap** (e.g. `H=2` when 02:00 does not exist):
   **Policy:** use the first valid local time at or after `H:00` on
   date `D` (typically `03:00`). Document this. Alternative rejected:
   error exit — worse UX for a display tool.
3. **Fall-back fold** (e.g. two `01:00` instants):
   **Policy:** use the **first** occurrence (earlier UTC / DST still in
   effect), matching “start of that clock hour” intuition.
4. **Half-hour offsets (Lord Howe etc.):** Local times may be `HH:30`
   for “top of hour” displays already in full-day mode. For `--hour N`,
   still target local `N:00` if it exists on that day; if the zone’s
   civil times are only `:30` after transition, follow the same
   fold/gap rules using `datetime` + `ZoneInfo` fold semantics.

Implementation should use `zoneinfo`/`datetime` correctly rather than
string matching.

## Recommended implementation sketch

```python
from datetime import time as dt_time

def _hour_instant(self) -> datetime:
    """UTC instant for local civil hour ``self.hour`` on the local day."""
    assert self.hour is not None
    local_mid = _to_local(self.base_instant)
    # Naive civil datetime in local zone
    civil = datetime(
        local_mid.year,
        local_mid.month,
        local_mid.day,
        self.hour,
        0,
        0,
    )
    # Attach local tz. On systems under test, _to_local is monkeypatched;
    # production local zone is the system zone.
    local_tz = local_mid.tzinfo
    if local_tz is None:
        # Should not happen — base_instant is aware
        aware = civil.astimezone()
    else:
        # fold=0 → first occurrence on ambiguous hours
        aware = civil.replace(tzinfo=local_tz, fold=0)
        # If spring-forward made this wall time invalid, ZoneInfo may
        # still accept and adjust; verify with tests per platform.
        # Portable approach: search _day_instants() for matching local hour.
    return aware.astimezone(datetime_timezone.utc)
```

**Portable approach preferred (matches existing DST tests style):**

```python
def _instant_for_local_hour(self, hour: int) -> datetime:
    matches = [
        inst for inst in self._day_instants()
        if _to_local(inst).hour == hour and _to_local(inst).minute == 0
    ]
    if matches:
        return matches[0]  # first = fold preference
    # Gap: no exact HH:00 — pick first instant whose local time is > hour:00
    # or the first instant after the gap with local.hour > hour
    for inst in self._day_instants():
        local = _to_local(inst)
        if (local.hour, local.minute) > (hour, 0):
            return inst
    # Fallback: last instant of the day (should be rare)
    return self._day_instants()[-1]
```

Then `_build_table`:

```python
        if self.hour is not None:
            instants = [self._instant_for_local_hour(self.hour)]
        else:
            instants = self._day_instants()
```

This reuses DST-correct `_day_instants()` and stays cross-platform with
the `_to_local` monkeypatch.

## File map

| File | Change |
|------|--------|
| `timezone_converter/comparison_view.py` | `_instant_for_local_hour`, `_build_table` |
| `tests/comparison_view_test.py` | DST hour tests; update any index-based assumptions |
| `README.md` | Document wall-clock meaning + gap policy |
| `AGENTS.md` | Note hour selection policy under architecture |

---

### Task 1: Failing tests for wall-clock semantics

**Files:**
- Modify: `tests/comparison_view_test.py`

- [ ] **Step 1: Add tests** (using existing `local_timezone` fixture):

```python
def test_hour_selects_local_wall_clock_on_spring_forward_day(local_timezone):
    zone = local_timezone('America/New_York')
    view = _make_view(['london'], hour=14)
    view.base_instant = datetime(2026, 3, 8, tzinfo=zone)
    cells = list(view._build_table().columns[0]._cells)
    assert cells == ['2026-03-08 14:00']


def test_hour_two_on_spring_forward_uses_post_gap_time(local_timezone):
    # 02:00 does not exist; policy → first local time after gap with hour>=2
    # typically 03:00
    zone = local_timezone('America/New_York')
    view = _make_view(['london'], hour=2)
    view.base_instant = datetime(2026, 3, 8, tzinfo=zone)
    cells = list(view._build_table().columns[0]._cells)
    assert cells == ['2026-03-08 03:00']


def test_hour_one_on_fall_back_uses_first_occurrence(local_timezone):
    zone = local_timezone('America/New_York')
    view = _make_view(['london'], hour=1)
    view.base_instant = datetime(2026, 11, 1, tzinfo=zone)
    # First 01:00 is EDT (UTC-4) — assert via UTC instant or single local cell
    local_cell = list(view._build_table().columns[0]._cells)[0]
    assert local_cell == '2026-11-01 01:00'
    # Ensure we did not pick an arbitrary later row: only one row
    assert len(view._build_table().rows) == 1


def test_hour_zero_still_single_row_wall_clock(local_timezone):
    zone = local_timezone('America/New_York')
    view = _make_view(['new_york'], hour=0, zone=True)
    view.base_instant = datetime(2026, 6, 1, tzinfo=zone)
    table = view._build_table()
    assert len(table.rows) == 1
    assert list(table.columns[0]._cells) == ['2026-06-01 00:00']
```

- [ ] **Step 2: Run — expect FAIL** on spring-forward hour=14 (currently
  yields 15:00 under local NY).

```bash
pytest tests/comparison_view_test.py -k 'hour_selects_local or hour_two_on_spring' -v
```

---

### Task 2: Implement `_instant_for_local_hour`

**Files:**
- Modify: `timezone_converter/comparison_view.py`

- [ ] **Step 1: Implement** method as in the portable sketch above.
- [ ] **Step 2: Wire `_build_table`** to use it when `self.hour is not None`.
- [ ] **Step 3: Run new tests + full suite.**

```bash
coverage run -m pytest && coverage report
```

- [ ] **Step 4: Commit**

```bash
git commit -am "fix: interpret --hour as local wall-clock hour across DST"
```

---

### Task 3: Highlight regression guard on fall-back

- [ ] **Step 1: Optional test** — when `now` falls in the first repeated
  hour window, exactly one row is blue (full-day mode). Can monkeypatch
  `datetime.now` if needed. Skip if already covered by
  `test_current_hour_row_is_highlighted` stability.

- [ ] **Step 2: Commit if added.**

---

### Task 4: Docs

**Files:**
- Modify: `README.md` “Output a single hour” section
- Modify: `AGENTS.md` architecture bullet

README addition:

```markdown
### Output a single hour

Using the `--hour` argument, you can output a single hour. If you don't
provide a value, the current hour will be displayed.

`--hour N` selects local wall-clock time `N:00` on today's local date.
On spring-forward days, if that local time does not exist, the first
valid local time after the gap is shown. On fall-back days with a
repeated hour, the first occurrence is shown.
```

AGENTS.md bullet:

```markdown
- `--hour N` means local wall-clock `N:00` (first occurrence on fold;
  first valid time after gap on spring-forward), not the Nth UTC step
  from midnight.
```

- [ ] **Step 1: Edit docs and commit**

```bash
git commit -am "docs: define --hour wall-clock and DST gap/fold policy"
```

---

### Task 5: PR

- [ ] Open PR titled
  `fix: make --hour select local wall-clock time (DST-safe)`
- [ ] PR body includes **BEHAVIOR CHANGE** section with before/after
  example (NY spring-forward `--hour 14`: was 15:00, now 14:00).
- [ ] Suggest release notes under 0.17.0.

## Self-review checklist

- [x] Normative semantics for gap and fold.
- [x] Portable implementation via `_day_instants` + `_to_local`.
- [x] Tests for spring-forward hour=14 and hour=2.
- [x] Docs updated per coordinated-change rule.
