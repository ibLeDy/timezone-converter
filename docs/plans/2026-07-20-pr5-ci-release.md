# PR 5: CI, release graph, Dependabot, security docs

> **For agentic workers:** Prefer careful, reviewable CI edits. Do not
> rotate secrets. Checkbox tracking.

**Status:** Proposed
**Goal:** Reduce supply-chain and half-publish risk; add dependency
automation; document security and changelog expectations.
**Architecture:** Split `deployment.yml` into ordered jobs; add
Dependabot; light docs.
**Tech stack:** GitHub Actions, Docker Buildx, existing tox.

## Global constraints

See roadmap. No application runtime change. Depends on PR 1
`.dockerignore` for sensible Docker context (can cherry-pick
dockerignore if this PR lands first).

## Design decisions

1. **Dependabot** for `github-actions` and `pip` (weekly). Pre-commit
   already monthly via pre-commit.ci.
2. **Release jobs:**
   - `test` — checkout, setup Python, version gate, install, coverage.
   - `pypi` — needs: test; build + publish (OIDC, environment release).
   - `docker` — needs: test; build/push (can run **parallel** with pypi
     after test).
   **Half-publish note:** PyPI and Docker can still diverge if one fails
   after both start. **Stricter option (recommended):**
   `docker` needs `test`; `pypi` needs `test` **and** `docker`
   so Docker must succeed before PyPI (or reverse: PyPI first is current
   risk).
   **Chosen default for this plan:**
   `test` → then **parallel** `docker` + build artifact; **`pypi` needs
   both `test` and a `docker` job that builds (and pushes) successfully.**
   Trade-off: Docker Hub outage blocks PyPI. Acceptable for this project
   size; document in RELEASE.md.
   Alternative if maintainer prefers PyPI-first: keep order but add
   failure notification only — note in PR if overridden.
3. **Docker smoke:** After build/push (or on a local load for single-arch
   smoke before push), run:

   ```bash
   docker run --rm bledy/timezone-converter:… --version
   docker run --rm bledy/timezone-converter:… tijuana --hour 12
   ```

   Multi-arch push makes “run” ambiguous; **smoke on `linux/amd64`
   via buildx `--load` in a dedicated step on ubuntu-latest** before
   multi-arch push, or smoke against the published amd64 digest after
   push. **Chosen:** build amd64 with `--load`, smoke, then multi-arch
   push.
4. **Action SHA pins:** Optional stretch. With Dependabot on
   `github-actions`, version tags are acceptable for this PR; add a
   short comment in RELEASE.md that SHA pinning is optional hardening.
5. **`develop` branch trigger:** Keep unless maintainer confirms
   unused; document in PR.
6. **Python 3.14:** Add to matrix only if `actions/setup-python` and
   tox env work on all OS runners at implementation time; otherwise open
   a follow-up issue and skip.

## File map

| File | Change |
|------|--------|
| `.github/workflows/deployment.yml` | job graph + docker smoke |
| `.github/workflows/integration.yml` | optional 3.14; develop note |
| `.github/dependabot.yml` | create |
| `SECURITY.md` | create |
| `CHANGELOG.md` | create skeleton |
| `RELEASE.md` | job order + changelog reminder |
| `Dockerfile` | optional comment only; no digest pin required |

---

### Task 1: Dependabot

**Files:**
- Create: `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5

  - package-ecosystem: pip
    directory: /
    schedule:
      interval: monthly
    open-pull-requests-limit: 5
```

- [ ] **Step 1: Add file and commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: enable Dependabot for Actions and pip"
```

---

### Task 2: Restructure deployment workflow

**Files:**
- Modify: `.github/workflows/deployment.yml`
- Modify: `RELEASE.md`

- [ ] **Step 1: Rewrite jobs** approximately as:

```yaml
name: deployment

on:
  release:
    types:
      - published

permissions:
  contents: read
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest
    environment: release
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Validate release version
        run: |
          python - <<'PY'
          # same version check as today
          PY
      - name: Install and test
        run: |
          python -m pip install --upgrade pip build -e . -r requirements-dev.txt
          coverage run -m pytest && coverage report

  docker:
    needs: test
    runs-on: ubuntu-latest
    environment: release
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: bledy/timezone-converter
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest,enable=${{ github.event.release.prerelease == false }}
      - name: Build amd64 for smoke
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64
          load: true
          tags: timezone-converter:smoke
      - name: Smoke test image
        run: |
          docker run --rm timezone-converter:smoke --version
          docker run --rm timezone-converter:smoke tijuana --hour 12
      - name: Build and push multi-arch
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  pypi:
    needs: [test, docker]
    runs-on: ubuntu-latest
    environment: release
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install build tools
        run: python -m pip install --upgrade pip build -e . -r requirements-dev.txt
      - name: Build
        run: python -m build --sdist --wheel --outdir=dist/ .
      - name: Publish
        uses: pypa/gh-action-pypi-publish@release/v1
```

Adjust `environment: release` placement so OIDC and Docker secrets still
work (both jobs that need secrets get the environment).

- [ ] **Step 2: Update RELEASE.md** “Automated publishing” section to
  describe job order: test → docker (smoke + push) → PyPI.

- [ ] **Step 3: Commit**

```bash
git commit -am "ci: gate PyPI on tests and Docker smoke/push"
```

---

### Task 3: SECURITY.md and CHANGELOG.md

**Files:**
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`
- Modify: `RELEASE.md` (link CHANGELOG update step)

`SECURITY.md` minimal:

```markdown
# Security Policy

## Supported versions

The latest release on PyPI is supported with security fixes.

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub Security Advisories
for this repository (Security → Advisories → New draft advisory), or
email the maintainer address listed on PyPI/GitHub.

Do not open public issues for unfixed vulnerabilities.
```

`CHANGELOG.md` skeleton:

```markdown
# Changelog

All notable changes to this project are documented in this file.

Format inspired by Keep a Changelog. Versions match `pyproject.toml`
and Git tags.

## Unreleased

### Fixed
### Added
### Changed
### Security
```

RELEASE.md bullet under “Before creating the release”:

```markdown
- Update `CHANGELOG.md` (move Unreleased notes into the new version).
```

- [ ] **Step 1: Add files, commit**

```bash
git add SECURITY.md CHANGELOG.md RELEASE.md
git commit -m "docs: add SECURITY policy and changelog skeleton"
```

---

### Task 4: Integration matrix hygiene

**Files:**
- Modify: `.github/workflows/integration.yml` only if adding 3.14

- [ ] **Step 1: Probe 3.14 availability** during implementation. If
  available on ubuntu/mac/windows:

```yaml
python-version: [3.9, "3.10", "3.11", "3.12", "3.13", "3.14"]
```

And tox `envlist` + `gh-actions` mapping + classifier in pyproject.

If not available on all OS, **skip** and leave a short note in the PR
body / CHANGELOG Unreleased “Planned”.

- [ ] **Step 2: Commit only if 3.14 added.**

---

### Task 5: Verification

- [ ] Validate YAML:

```bash
# if actionlint available
actionlint .github/workflows/*.yml || true
python -c "import yaml,sys; yaml.safe_load(open('.github/dependabot.yml'))"
```

- [ ] Open PR
  `ci: Dependabot, safer release graph, security and changelog docs`

## Out-of-band (do not automate in this PR)

- Delete stale remote branches (`claude/*`, old features) after human review.
- Rotate Docker Hub tokens.
- Pin base image digests (optional follow-up).

## Self-review checklist

- [x] Half-publish risk addressed via job `needs`.
- [x] Docker smoke defined.
- [x] Dependabot + SECURITY + CHANGELOG.
- [x] 3.14 gated on runner reality.
