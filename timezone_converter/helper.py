from typing import Dict
from typing import Optional
from typing import Union

import pytz
from rich.columns import Columns
from rich.console import Console
from rich.table import Table


class Helper:
    # Short, human-friendly names (the lowercased last path segment). When
    # several zones share a segment the last one wins, matching pytz's sort
    # order; the shadowed zones stay reachable via their full path below.
    timezone_translations: Dict[str, str] = {
        tz.lower().split('/')[-1]: tz for tz in pytz.all_timezones
    }

    # Every canonical name keyed by its full, lowercased path so that no zone
    # is unreachable (e.g. both Asia/Istanbul and Europe/Istanbul).
    _canonical_paths: Dict[str, str] = {tz.lower(): tz for tz in pytz.all_timezones}

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
