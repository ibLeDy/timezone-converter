from datetime import datetime
from datetime import timedelta
from typing import Tuple

import pytz
from rich.table import Table

from timezone_converter.helper import Helper


class ComparisonView(Helper):
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
            pytz.timezone(self.timezone_name),
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
