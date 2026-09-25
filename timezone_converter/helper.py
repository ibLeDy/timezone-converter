import os
from collections import Counter
from datetime import tzinfo
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from zoneinfo import available_timezones
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from rich.columns import Columns
from rich.console import Console
from rich.table import Table

_ALL_TIMEZONES = sorted(available_timezones())
_TIMEZONE_TRANSLATIONS: Dict[str, str] = {
    tz.lower().split('/')[-1]: tz for tz in _ALL_TIMEZONES
}
_CANONICAL_PATHS: Dict[str, str] = {tz.lower(): tz for tz in _ALL_TIMEZONES}
_TIMEZONE_SEGMENTS = [tz.lower().split('/')[-1] for tz in _ALL_TIMEZONES]
_AMBIGUOUS_SEGMENTS = {
    segment for segment, count in Counter(_TIMEZONE_SEGMENTS).items() if count > 1
}
_AVAILABLE_TIMEZONES = sorted(
    set(_TIMEZONE_TRANSLATIONS).union(
        tz.lower()
        for tz in _ALL_TIMEZONES
        if tz.lower().split('/')[-1] in _AMBIGUOUS_SEGMENTS
    ),
)
_SEARCHABLE_TIMEZONES = sorted(set(_AVAILABLE_TIMEZONES).union(_CANONICAL_PATHS))


def local_timezone() -> Optional[tzinfo]:
    """Resolve the local timezone from the ``TZ`` environment variable.

    Containers and CI runners usually have no timezone of their own, so ``TZ``
    is the conventional way to tell them one. Resolving it through
    :mod:`zoneinfo` rather than the C library keeps the result identical on
    every platform: the C library needs the operating system's copy of the
    timezone database, which slim container images often omit and Windows does
    not have at all, and when that lookup fails it silently reinterprets a name
    like ``Europe/Madrid`` as a POSIX rule, yielding a zone abbreviated
    ``Europe`` at UTC+0 instead of an error.

    Returns
    -------
    Optional[tzinfo]
        The zone named by ``TZ``, or ``None`` when ``TZ`` is unset or does not
        name an IANA zone, meaning the platform's own local timezone should be
        used. Falling back covers the POSIX rule strings that ``TZ`` also
        accepts (``CET-1CEST,M3.5.0,M10.5.0/3``), which the C library
        understands and :mod:`zoneinfo` does not.
    """
    # POSIX allows a leading colon before the zone name, as in ``:Europe/Madrid``.
    name = os.environ.get('TZ', '').strip().removeprefix(':')
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


class Helper:
    """Base class providing timezone lookup and Rich rendering for views.

    Subclasses (:class:`~timezone_converter.comparison_view.ComparisonView`,
    :class:`~timezone_converter.list_view.ListView`, and
    :class:`~timezone_converter.search_view.SearchView`) inherit the
    timezone name tables and helper methods defined here.
    """

    # Short, human-friendly names (the lowercased last path segment). When
    # several zones share a segment the last one wins, matching sorted IANA
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
        """Resolve a user-supplied timezone name to its canonical IANA path.

        Parameters
        ----------
        name : str
            A timezone name as typed by the user: a short alias
            (``new_york``), a full canonical path (``America/New_York``),
            or any case variant of either.

        Returns
        -------
        Optional[str]
            The canonical IANA timezone path (e.g. ``America/New_York``),
            or ``None`` if `name` does not match any known timezone.
        """
        # Exact canonical paths win over the lossy short-name map so that a
        # top-level zone (e.g. Kwajalein) is not shadowed by another zone's
        # last segment (Pacific/Kwajalein).
        key = name.lower()
        return cls._canonical_paths.get(key) or cls.timezone_translations.get(key)

    @staticmethod
    def _print_with_rich(obj: Union[str, Columns, Table]) -> None:
        Console().print(obj)

    @classmethod
    def ambiguous_alternatives(cls, name: str) -> List[str]:
        """List the canonical paths a short timezone name could mean.

        Parameters
        ----------
        name : str
            A timezone name as typed by the user.

        Returns
        -------
        List[str]
            Every canonical IANA path sharing `name` as its last path
            segment, sorted, when there is more than one; otherwise an
            empty list. A name given as a full canonical path is never
            ambiguous, since it already says which zone is meant.
        """
        key = name.lower()
        if key in cls._canonical_paths or key not in _AMBIGUOUS_SEGMENTS:
            return []
        return sorted(
            timezone
            for timezone in _ALL_TIMEZONES
            if timezone.lower().split('/')[-1] == key
        )

    @staticmethod
    def _print_plain(text: str) -> None:
        # The one output that must not go through Rich: machine-readable
        # payloads, where wrapping, highlighting or markup interpretation
        # would corrupt what a consumer has to parse.
        print(text)

    @staticmethod
    def _print_error_with_rich(obj: Union[str, Columns, Table]) -> None:
        # Errors belong on stderr so a caller can redirect or pipe the real
        # output without swallowing the reason it is empty.
        Console(stderr=True).print(obj)
