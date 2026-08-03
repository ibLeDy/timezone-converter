# PR 2: Packaging markers and module entry

> **For agentic workers:** Implement task-by-task with TDD where
> behavior is observable. Checkbox (`- [ ]`) tracking.

**Status:** Proposed
**Goal:** Make packaging claims honest (`Typing :: Typed`), support
`python -m timezone_converter`, and modernize dev extras.
**Architecture:** Add static package data (`py.typed`, `__main__.py`);
extend `pyproject.toml` only. No timezone math changes.
**Tech stack:** hatchling, importlib.metadata, existing entry points.

## Global constraints

See roadmap. Prefer no version bump (packaging fix). If you flip the
Development Status classifier to Production/Stable, call that out in
the PR body as an intentional product decision.

## File map

| File | Change |
|------|--------|
| `timezone_converter/py.typed` | Create empty marker (PEP 561) |
| `timezone_converter/__main__.py` | `sys.exit(main())` |
| `pyproject.toml` | optional-deps `dev`; tox smoke for `-m timezone_converter`; optional classifier |
| `tests/main_test.py` or new `tests/package_test.py` | entry / marker tests if useful |
| `AGENTS.md` | document `python -m timezone_converter` once implemented |
| `README.md` | optional one-liner under Installation for module form |

---

### Task 1: `py.typed` marker

**Files:**
- Create: `timezone_converter/py.typed`
- Verify: hatch wheel includes package data by default for package dir

- [ ] **Step 1: Create empty file** `timezone_converter/py.typed`
  (zero bytes or a single blank line is fine; empty is conventional).

- [ ] **Step 2: Confirm hatch includes it**

```bash
pip install -e . build
python -m build --wheel --outdir=/tmp/tzc-dist
python - <<'PY'
import zipfile
from pathlib import Path
wheels = list(Path('/tmp/tzc-dist').glob('*.whl'))
assert wheels, 'no wheel'
with zipfile.ZipFile(wheels[0]) as zf:
    names = zf.namelist()
assert any(n.endswith('timezone_converter/py.typed') for n in names), names
print('py.typed in wheel OK')
PY
```

Expected: prints `py.typed in wheel OK`.

If the marker is missing from the wheel, add under
`[tool.hatch.build.targets.wheel]`:

```toml
[tool.hatch.build.targets.wheel]
packages = [
    "timezone_converter",
]
# only if needed — hatchling normally includes package data next to modules
```

Or set:

```toml
[tool.hatch.build]
include = [
  "timezone_converter/py.typed",
]
```

Only if Step 2 fails.

- [ ] **Step 3: Commit**

```bash
git add timezone_converter/py.typed
git commit -m "fix: ship PEP 561 py.typed marker for Typing :: Typed"
```

---

### Task 2: `__main__.py` entry

**Files:**
- Create: `timezone_converter/__main__.py`
- Modify: `tests/main_test.py` (add test)
- Modify: `pyproject.toml` tox commands
- Modify: `AGENTS.md`

- [ ] **Step 1: Write failing test** in `tests/main_test.py`:

```python
import subprocess
import sys


def test_python_module_package_entry_runs_help():
    proc = subprocess.run(
        [sys.executable, '-m', 'timezone_converter', '--help'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert 'timezone-converter' in proc.stdout
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/main_test.py::test_python_module_package_entry_runs_help -v
```

Expected: fail with `No module named timezone_converter.__main__` (or
non-zero returncode).

- [ ] **Step 3: Implement** `timezone_converter/__main__.py`:

```python
from timezone_converter.main import main

if __name__ == '__main__':
    raise SystemExit(main())
```

Use `raise SystemExit(main())` rather than bare `exit()` for consistency
with library-friendly module execution.

- [ ] **Step 4: Run test — expect PASS**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/main_test.py::test_python_module_package_entry_runs_help -v
```

- [ ] **Step 5: Add tox smoke** in `pyproject.toml` `[tool.tox]`
  `commands` list (after existing smokes):

```
    python -m timezone_converter --help
    tzconv --version
```

(`tzconv --version` may already exist; do not duplicate.)

- [ ] **Step 6: Update AGENTS.md** Commands:

```markdown
- Run: `timezone-converter` / `tzconv` `<timezone> [...]` or
  `python -m timezone_converter` (equivalent to
  `python -m timezone_converter.main`)
```

- [ ] **Step 7: Full suite + commit**

```bash
coverage run -m pytest && coverage report
git add timezone_converter/__main__.py tests/main_test.py pyproject.toml AGENTS.md CLAUDE.md
git commit -m "feat: support python -m timezone_converter via __main__"
```

---

### Task 3: Optional dev dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements-dev.txt` (keep as thin wrapper or mirror)
- Modify: `AGENTS.md` install line
- Modify: `RELEASE.md` if it mentions only requirements-dev

- [ ] **Step 1: Add to `pyproject.toml`:**

```toml
[project.optional-dependencies]
dev = [
    "covdefaults",
    "coverage",
    "pre-commit",
    "pytest",
    "tox",
    "tox-gh-actions",
]
```

Keep `requirements-dev.txt` in sync (same pins/unpinned list) so
existing docs keep working:

```
# Mirror of [project.optional-dependencies] dev — prefer:
#   pip install -e ".[dev]"
covdefaults
coverage
pre-commit
pytest
tox
tox-gh-actions
```

- [ ] **Step 2: Update AGENTS install line:**

```markdown
- Install: `pip install -e ".[dev]"` (or `pip install -e .` and
  `pip install -r requirements-dev.txt`)
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml requirements-dev.txt AGENTS.md CLAUDE.md RELEASE.md
git commit -m "chore: add optional dev extras matching requirements-dev"
```

---

### Task 4: Development Status classifier (decision)

**Files:**
- Modify: `pyproject.toml` classifiers (optional)

- [ ] **Step 1: Decide with maintainer default:**
  **Recommended:** change to
  `"Development Status :: 5 - Production/Stable"`
  given multi-year releases, 100% coverage, and multi-OS CI.
  If the maintainer prefers staying Beta until PR 4 ships, **skip**
  this task and note it in the PR body.

- [ ] **Step 2: If changing:**

```toml
    "Development Status :: 5 - Production/Stable",
```

- [ ] **Step 3: Commit**

```bash
git commit -am "chore: mark Development Status as Production/Stable"
```

---

### Task 5: Verification

- [ ] **Step 1:**

```bash
coverage run -m pytest && coverage report
pre-commit run --all-files
python -m timezone_converter --help
tzconv --version   # after reinstall: pip install -e ".[dev]"
```

- [ ] **Step 2: Open PR**
  `fix: packaging py.typed, __main__, and dev extras`

---

## Self-review checklist

- [x] `Typing :: Typed` honesty via `py.typed`.
- [x] Module execution path covered by test + tox.
- [x] Dev extras do not replace runtime deps.
