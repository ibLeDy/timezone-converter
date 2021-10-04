from difflib import get_close_matches
from typing import List

from timezone_converter.helper import Helper


class SearchView(Helper):
    def __init__(self, search: str) -> None:
        self.search = search

    def _search_and_sort(self, search: str) -> List[str]:
        timezones: List[str] = get_close_matches(
            search,
            self.timezone_translations,
        )

        if len(timezones) > 0:
            timezones.sort()

        # If the search term has a corresponding timezone, return it instead
        if search in timezones:
            timezones = [search]

        return timezones

    def print_search_results(self) -> int:
        timezones = self._search_and_sort(self.search)
        self._print_with_rich(
            'Found {} {}: {}'.format(
                len(timezones),
                'timezone' if len(timezones) == 1 else 'timezones',
                ', '.join(map(lambda tz: f'"{tz}"', timezones)),
            ),
        )
        return 0
