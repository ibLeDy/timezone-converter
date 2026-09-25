import pytest


@pytest.fixture(autouse=True)
def _no_tz_from_the_environment(monkeypatch):
    # ``TZ`` picks the local zone when --local is absent, so a developer's own
    # ``TZ`` would override the machine zone that most tests pin through the
    # ``_to_local`` seam. Start every test without it; tests about ``TZ`` set
    # it themselves.
    monkeypatch.delenv('TZ', raising=False)
