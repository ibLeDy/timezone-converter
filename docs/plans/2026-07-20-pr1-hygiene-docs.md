# PR 1: Hygiene, ignore files, docstring drift

> **For agentic workers:** Implement task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking. Keep this PR low-risk and free of
> behavior changes.

**Status:** Proposed
**Goal:** Fix doc drift, ignore-file bugs, and dead tooling without
changing CLI behavior.
**Architecture:** Config and comment-only edits plus docstring text;
no runtime logic changes.
**Tech stack:** existing pre-commit, git ignore, Markdown docs.

## Global constraints

See `docs/plans/2026-07-20-audit-remediation-roadmap.md`. No version bump.

## File map

| File | Change |
|------|--------|
| `.dockerignore` | Ignore `tests/`, agent docs, coverage junk; drop useless `test` |
| `.gitignore` | Coverage/cache artifacts |
| `.pre-commit-config.yaml` | Remove `setup-cfg-fmt` repo block |
| `timezone_converter/main.py` | Docstring: `--single` → `--hour`, list real flags |
| `timezone_converter/comparison_view.py` | Document `difference` param |
| `AGENTS.md` / `CLAUDE.md` | `tzconv`, `python -m timezone_converter` after PR 2 note as upcoming or list both entry forms |
| `README.md` | Only if a hygiene-related inaccuracy remains (usually none) |

---

### Task 1: Fix `.dockerignore`

**Files:**
- Modify: `.dockerignore`

- [ ] **Step 1: Replace contents** with:

```
.git
.github
.mypy_cache
.pre-commit-config.yaml
.pytest_cache
.venv
.tox
*.egg-info
build
dist
requirements-dev.txt
tests
docs
AGENTS.md
CLAUDE.md
RELEASE.md
.coverage
htmlcov
coverage.xml
.ruff_cache
```

Rationale: `test` never matched `tests/`; image was shipping the suite.
Keep `LICENSE` and `README.md` and package sources for `pip install .`.

- [ ] **Step 2: Sanity-check** (no Docker required if unavailable):

```bash
# From worktree root — list what would be sent as context (if docker installed)
docker build --dry-run . 2>/dev/null || python - <<'PY'
from pathlib import Path
text = Path('.dockerignore').read_text().splitlines()
assert 'tests' in text
assert 'test' not in text or any(line.strip() == 'tests' for line in text)
print('dockerignore ok')
PY
```

Expected: assertion passes.

- [ ] **Step 3: Commit**

```bash
git add .dockerignore
git commit -m "chore: exclude tests and docs from Docker build context"
```

---

### Task 2: Expand `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append** (keep existing entries):

```
.coverage
.coverage.*
htmlcov/
coverage.xml
.ruff_cache/
.dmypy.json
.DS_Store
```

Keep the existing bare `test` entry (legacy; does not ignore `tests/`).
Do **not** add `tests` to gitignore.

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore coverage and local tool caches"
```

---

### Task 3: Remove dead `setup-cfg-fmt` hook

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Delete** the entire repo block:

```yaml
  - repo: https://github.com/asottile/setup-cfg-fmt
    rev: v3.2.0
    hooks:
      - id: setup-cfg-fmt
        args:
          - "--include-version-classifiers"
```

(There is no `setup.cfg` in the project.)

- [ ] **Step 2: Run**

```bash
pre-commit run --all-files
```

Expected: hooks pass (or only pre-existing issues unrelated to this deletion).

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: drop unused setup-cfg-fmt pre-commit hook"
```

---

### Task 4: Fix docstrings

**Files:**
- Modify: `timezone_converter/main.py` (module docstring of `build_parser`)
- Modify: `timezone_converter/comparison_view.py` (`__init__` Parameters)

- [ ] **Step 1: Update `build_parser` docstring** to list actual flags:

```python
    """Build the command-line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured with the ``timezone``, ``--list``, ``--version``,
        ``--zone``, ``--hour``, ``--search``, ``--order``, and
        ``--difference`` arguments.
    """
```

- [ ] **Step 2: Add `difference` to `ComparisonView.__init__` Parameters**
  (after `order`):

```python
        order : bool
            If ``True``, sort the foreign timezones by absolute offset
            from the local timezone.
        difference : bool
            If ``True``, append each foreign column's signed hour offset
            from the local timezone to the header (e.g. ``+5h``).
```

- [ ] **Step 3: Commit**

```bash
git add timezone_converter/main.py timezone_converter/comparison_view.py
git commit -m "docs: align parser and ComparisonView docstrings with CLI"
```

---

### Task 5: Agent docs — entry points

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md` (keep in sync if it remains a full copy)

- [ ] **Step 1: Update Commands section** run line to:

```markdown
- Run: `timezone-converter` / `tzconv` `<timezone> [<timezone> ...]` or
  `python -m timezone_converter.main`
  (after packaging PR: also `python -m timezone_converter`)
```

If this PR merges **before** PR 2, document only what works today:

```markdown
- Run: `timezone-converter` or `tzconv` `<timezone> [...]`, or
  `python -m timezone_converter.main`
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md CLAUDE.md
git commit -m "docs: document tzconv entry point for agents"
```

---

### Task 6: Verify no behavior change

- [ ] **Step 1: Run tests**

```bash
pip install -e . -r requirements-dev.txt   # if needed
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 coverage run -m pytest
coverage report
```

Expected: 100% coverage, all pass.

- [ ] **Step 2: Open PR** titled roughly
  `chore: Docker/git ignore hygiene and docstring drift`
  Body links this plan and the roadmap. No behavior-change section needed.

---

## Self-review checklist

- [x] All PR 1 audit items mapped (dockerignore, gitignore, setup-cfg-fmt, docstrings, AGENTS).
- [x] No placeholders requiring “fill in later.”
- [x] No runtime behavior change intended.
