# Regenerate the example screenshots under .github/assets/.
#
# Re-runs the exact CLI commands shown in README.md through a recording Rich
# console and overwrites the corresponding SVG. Run this after any change to
# table/column layout, then review the diff before committing.
#
# Usage: python scripts/generate_assets.py
import sys
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple

from rich.console import Console

from timezone_converter import helper
from timezone_converter.main import main as run_main

ASSETS_DIR = Path(__file__).resolve().parent.parent / '.github' / 'assets'

# `width=None` measures the renderable's own natural width first and uses
# exactly that, so tables are tightly cropped instead of padded out to a
# fixed canvas. `--list` renders a `Columns` grid that expands to fill
# whatever width it's given rather than having one true natural width, so it
# gets an explicit value instead: Rich's SVG export always renders text at a
# fixed pixel size and README.md displays images at a fixed content width
# (roughly 830px), so a *wider* render doesn't make the text bigger on
# GitHub, it just gets shrunk down further to fit, becoming smaller. 160
# columns keeps the rendered text close to its natural on-screen size there,
# at the cost of a taller image with more rows.
COMMANDS: List[Tuple[str, List[str], Optional[int]]] = [
    ('tijuana_zone.svg', ['tijuana', '--zone'], None),
    ('tijuana_new_york.svg', ['tijuana', 'new_york'], None),
    ('list.svg', ['--list'], 160),
]


def _run(argv: List[str], console: Console) -> None:
    helper.Helper._print_with_rich = staticmethod(  # type: ignore[method-assign]
        lambda obj: console.print(obj),
    )
    sys.argv = ['timezone-converter', *argv]
    run_main()


def _natural_width(argv: List[str], probe_width: int = 200) -> int:
    probe = Console(record=True, width=probe_width)
    _run(argv, probe)
    lines = [line for line in probe.export_text().splitlines() if line.strip()]
    return max((len(line) for line in lines), default=probe_width)


def _render(argv: List[str], width: Optional[int]) -> Console:
    if width is None:
        width = _natural_width(argv)
    console = Console(record=True, width=width)
    _run(argv, console)
    return console


def main() -> None:
    for filename, argv, width in COMMANDS:
        console = _render(argv, width)
        title = '$ timezone-converter ' + ' '.join(argv)
        out_path = ASSETS_DIR / filename
        console.save_svg(str(out_path), title=title)
        print(f'wrote {out_path}')


if __name__ == '__main__':
    main()
