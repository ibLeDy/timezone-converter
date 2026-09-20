import re
import runpy
from importlib import metadata
from pathlib import Path

import pytest

import timezone_converter

PACKAGE_DIR = Path(timezone_converter.__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
REQUIREMENTS_DEV = REPO_ROOT / 'requirements-dev.txt'

# Which quotes the environment marker uses depends on the packaging version
# that built the metadata, so match either.
DEV_MARKER = re.compile(r'extra\s*==\s*[\'"]dev[\'"]')


def test_py_typed_ships_with_the_installed_package():
    # The ``Typing :: Typed`` classifier is only honest if PEP 561's marker
    # actually reaches the installed package. Checking the installed location
    # rather than the source tree means the tox runs, which install a built
    # wheel, are really checking the wheel.
    assert (PACKAGE_DIR / 'py.typed').is_file()


def test_module_entry_point_is_runnable(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['timezone-converter', '--help'])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module('timezone_converter', run_name='__main__')

    assert exit_info.value.code == 0
    assert 'usage' in capsys.readouterr().out


@pytest.mark.skipif(
    not REQUIREMENTS_DEV.is_file(),
    reason='requirements-dev.txt is not shipped in the distribution',
)
def test_dev_extra_mirrors_the_requirements_file():
    # Two places list the same development dependencies, so make drift
    # between them fail a test rather than surprise the next contributor.
    # Reading the *installed* metadata checks what the build actually
    # produced, not just what pyproject.toml says.
    requires = metadata.requires('timezone-converter') or []
    dev_extra = sorted(
        requirement.split(';')[0].strip()
        for requirement in requires
        if DEV_MARKER.search(requirement)
    )
    expected = sorted(
        line.strip()
        for line in REQUIREMENTS_DEV.read_text().splitlines()
        if line.strip()
    )

    assert dev_extra == expected
