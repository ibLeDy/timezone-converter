# Regenerate the example screenshots under .github/assets/.
#
# Re-runs the exact CLI commands shown in README.md through a recording Rich
# console and overwrites the corresponding SVG. Run this after any change to
# table/column layout, then review the diff before committing.
#
# Usage: python scripts/generate_assets.py
import inspect
import sys
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple

from rich.console import Console

from timezone_converter import helper
from timezone_converter.main import main as run_main

ASSETS_DIR = Path(__file__).resolve().parent.parent / '.github' / 'assets'

# Two portability fixes on top of Rich's default SVG template:
#
# 1. It only sets `viewBox` on the root <svg>, not width/height. The
#    previously committed assets (an older Rich version) had explicit
#    width/height, which some SVG consumers need for intrinsic sizing
#    rather than deriving it from viewBox alone.
# 2. Its rendered text uses `font-family: Fira Code, monospace`, and Fira
#    Code is only available via a `@font-face` pointing at a CDN. Any
#    viewer that can't load that (offline, or a sandboxed raw-file preview
#    that blocks external requests, e.g. GitHub's own SVG file viewer)
#    falls back to a font that may be missing Rich's box-drawing glyphs,
#    rendering them as placeholder boxes instead of table lines. Dropping
#    "Fira Code" from the rule that's actually used means the CDN is never
#    even requested, so the box-drawing characters always come from
#    whatever monospace font is actually available locally.
_DEFAULT_SVG_FORMAT = (
    inspect.signature(Console.export_svg).parameters['code_format'].default
)
_VIEWBOX_NEEDLE = 'viewBox="0 0 {width} {height}"'
_FONT_NEEDLE = 'font-family: Fira Code, monospace;'
assert _VIEWBOX_NEEDLE in _DEFAULT_SVG_FORMAT, 'Rich SVG template changed shape'
assert _FONT_NEEDLE in _DEFAULT_SVG_FORMAT, 'Rich SVG template changed shape'
SVG_FORMAT = _DEFAULT_SVG_FORMAT.replace(
    _VIEWBOX_NEEDLE,
    f'width="{{width}}" height="{{height}}" {_VIEWBOX_NEEDLE}',
    1,
).replace(
    _FONT_NEEDLE,
    "font-family: Consolas, Monaco, 'Courier New', monospace;",
    1,
)

# `width=None` measures the renderable's own natural width first and uses
# exactly that, so tables are tightly cropped instead of padded out to a
# fixed canvas. `--list` renders a `Columns` grid that expands to fill
# whatever width it's given rather than having one true natural width, so it
# gets an explicit value instead, chosen to keep roughly the same
# width:height proportions as the screenshot it replaces (which was
# ~1555x1292) rather than an extremely tall, narrow stack.
COMMANDS: List[Tuple[str, List[str], Optional[int]]] = [
    ('tijuana_zone.svg', ['tijuana', '--zone'], None),
    ('tijuana_new_york.svg', ['tijuana', 'new_york'], None),
    ('list.svg', ['--list'], 360),
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
        console.save_svg(str(out_path), title=title, code_format=SVG_FORMAT)
        print(f'wrote {out_path}')


if __name__ == '__main__':
    main()
