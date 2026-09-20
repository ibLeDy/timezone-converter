## Summary

<!-- What and why. Link issues with Fixes #N / Refs #N. -->

## Test plan

- [ ] `coverage run -m pytest && coverage report` (100%)
- [ ] `pre-commit run --all-files` (or CI equivalent)
- [ ] CLI smoke for any new/changed flags (see tox commands in `pyproject.toml`)

## Checklist

- [ ] Coordinated docs if CLI flags or behavior changed (README, AGENTS if needed)
- [ ] DST-sensitive changes include spring-forward and fall-back tests
- [ ] No secrets or local paths committed

## Breaking change?

- [ ] No
- [ ] Yes — describe migration / label `breaking`
