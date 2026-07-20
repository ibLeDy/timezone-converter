"""Fuzzy-search available timezone names for a search term."""

from difflib import get_close_matches
from typing import List

from timezone_converter.helper import Helper


class SearchView(Helper):
    """Fuzzy-match a search term against the available timezone names."""

    def __init__(self, search: str) -> None:
        self.search = search.lower()

    def _search_and_sort(self, search: str) -> List[str]:
        timezones: List[str] = get_close_matches(
            search,
            self.searchable_timezones,
        )
        timezones.sort()

        # If the search term has a corresponding timezone, return it instead
        if search in timezones:
            timezones = [search]

        return timezones

    def print_search_results(self) -> int:
        """Print the fuzzy search results to the console.

        Returns
        -------
        int
            Always ``0``.
        """
        timezones = self._search_and_sort(self.search)
        self._print_with_rich(
            'Found {} {}: {}'.format(
                len(timezones),
                'timezone' if len(timezones) == 1 else 'timezones',
                ', '.join(map(lambda tz: f'"{tz}"', timezones)),
            ),
        )
        return 0
