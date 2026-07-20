"""Regenerate the example screenshots under .github/assets/.

Re-runs the exact CLI commands shown in README.md through a recording Rich
console and overwrites the corresponding SVG. Run this after any change to
table/column layout, then review the diff before committing.

Usage: python scripts/generate_assets.py
"""
import sys
from pathlib import Path
from typing import List
from typing import Tuple

from rich.console import Console

from timezone_converter import helper
from timezone_converter.main import main as run_main

ASSETS_DIR = Path(__file__).resolve().parent.parent / '.github' / 'assets'

COMMANDS: List[Tuple[str, List[str]]] = [
    ('tijuana_zone.svg', ['tijuana', '--zone']),
    ('tijuana_new_york.svg', ['tijuana', 'new_york']),
    ('list.svg', ['--list']),
]


def _render(argv: List[str]) -> Console:
    console = Console(record=True, width=120)
    helper.Helper._print_with_rich = staticmethod(  # type: ignore[method-assign]
        lambda obj: console.print(obj),
    )
    sys.argv = ['timezone-converter', *argv]
    run_main()
    return console


def main() -> None:
    for filename, argv in COMMANDS:
        console = _render(argv)
        title = '$ timezone-converter ' + ' '.join(argv)
        out_path = ASSETS_DIR / filename
        console.save_svg(str(out_path), title=title)
        print(f'wrote {out_path}')


if __name__ == '__main__':
    main()
