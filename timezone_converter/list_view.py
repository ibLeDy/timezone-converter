from collections import defaultdict
from typing import DefaultDict
from typing import List

from rich.columns import Columns
from rich.panel import Panel

from timezone_converter.helper import Helper


class ListView(Helper):
    def _sort_and_group(self) -> DefaultDict[str, List[str]]:
        sorted_timezones = dict(sorted(self.timezone_translations.items()))
        longest_name = len(max(sorted_timezones, key=lambda x: len(x)))
        timezone_groups = defaultdict(list)
        for tz_name in sorted_timezones:
            timezone_groups[tz_name[0]].append(tz_name.center(longest_name))

        return timezone_groups

    def _build_columns(self) -> Columns:
        timezone_groups = self._sort_and_group()
        panels = [
            Panel('\n'.join(timezone_groups[group]), title=group.upper())
            for group in timezone_groups
            if timezone_groups[group]
        ]

        return Columns(panels, expand=True)

    def print_columns(self) -> None:
        self._print_with_rich(self._build_columns())
