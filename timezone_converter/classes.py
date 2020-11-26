from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from typing import DefaultDict
from typing import List
from typing import Tuple
from typing import Union

import pytz
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class Helper:
    timezone_translations = {tz.lower().split('/')[-1]: tz for tz in pytz.all_timezones}

    @staticmethod
    def _print_with_rich(rich_object: Union[Columns, Table]) -> None:
        Console().print(rich_object)


class TimezonesComparison(Helper):
    def __init__(self, timezone: str, zone: bool) -> None:
        self.timezone = timezone
        self.zone = zone
        self.timezone_name = self._get_timezone_name(self.timezone)
        self.current_dt = datetime.now()
        self.local_midnight = datetime(
            self.current_dt.year,
            self.current_dt.month,
            self.current_dt.day,
        ).astimezone()
        self.foreign_midnight = self.local_midnight.astimezone(
            pytz.timezone(self.timezone_name)
        )

    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.timezone_translations.get(timezone.lower())
        if timezone_name is None:
            raise SystemExit(f'error: {timezone !r} is not an available timezone')
        return timezone_name

    def _get_headers(self) -> Tuple[str, str]:
        local_header = 'LOCAL'
        foreign_header = str(self.foreign_midnight.tzinfo).upper()

        if self.zone:
            local_header += f' ({self.local_midnight.tzname()})'
            foreign_header += f' ({self.foreign_midnight.tzname()})'

        return local_header, foreign_header

    def _build_table(self) -> Table:
        local_header, foreign_header = self._get_headers()
        table = Table()
        table.add_column(local_header, justify='center')
        table.add_column(foreign_header, justify='center')

        fmt = '%Y-%m-%d %H:%M'
        for hour in range(24):
            table.add_row(
                (self.local_midnight + timedelta(hours=hour)).strftime(fmt),
                (self.foreign_midnight + timedelta(hours=hour)).strftime(fmt),
            )

        return table

    def print_table(self) -> None:
        self._print_with_rich(self._build_table())


class TimezonesList(Helper):
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
