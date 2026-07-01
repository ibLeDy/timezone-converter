from collections import Counter
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pytz
from rich.columns import Columns
from rich.console import Console
from rich.table import Table


_TIMEZONE_TRANSLATIONS: Dict[str, str] = {
    tz.lower().split('/')[-1]: tz for tz in pytz.all_timezones
}
_CANONICAL_PATHS: Dict[str, str] = {tz.lower(): tz for tz in pytz.all_timezones}
_TIMEZONE_SEGMENTS = [tz.lower().split('/')[-1] for tz in pytz.all_timezones]
_AMBIGUOUS_SEGMENTS = {
    segment for segment, count in Counter(_TIMEZONE_SEGMENTS).items() if count > 1
}
_AVAILABLE_TIMEZONES = sorted(
    set(_TIMEZONE_TRANSLATIONS).union(
        tz.lower()
        for tz in pytz.all_timezones
        if tz.lower().split('/')[-1] in _AMBIGUOUS_SEGMENTS
    ),
)
_SEARCHABLE_TIMEZONES = sorted(set(_AVAILABLE_TIMEZONES).union(_CANONICAL_PATHS))


class Helper:
    # Short, human-friendly names (the lowercased last path segment). When
    # several zones share a segment the last one wins, matching pytz's sort
    # order; the shadowed zones stay reachable via their full path below.
    timezone_translations: Dict[str, str] = _TIMEZONE_TRANSLATIONS

    # Every canonical name keyed by its full, lowercased path so that no zone
    # is unreachable (e.g. both Asia/Istanbul and Europe/Istanbul).
    _canonical_paths: Dict[str, str] = _CANONICAL_PATHS

    # User-facing names for list/search. Most zones keep their short friendly
    # alias; canonical paths are added when the short alias is ambiguous.
    available_timezones: List[str] = _AVAILABLE_TIMEZONES

    # Search/suggestion names include every canonical path so full timezone
    # names can be found without making the list output noisy.
    searchable_timezones: List[str] = _SEARCHABLE_TIMEZONES

    @classmethod
    def resolve_timezone(cls, name: str) -> Optional[str]:
        # Exact canonical paths win over the lossy short-name map so that a
        # top-level zone (e.g. Kwajalein) is not shadowed by another zone's
        # last segment (Pacific/Kwajalein).
        key = name.lower()
        return cls._canonical_paths.get(key) or cls.timezone_translations.get(key)

    @staticmethod
    def _print_with_rich(obj: Union[str, Columns, Table]) -> None:
        Console().print(obj)
