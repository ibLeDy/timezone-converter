from datetime import datetime
from datetime import timedelta
from typing import List

import pytz
from rich.table import Table

from timezone_converter.helper import Helper


class ComparisonView(Helper):
    def __init__(self, timezones: List[str], zone: bool) -> None:
        self.zone = zone

        current_dt = datetime.now()
        local_midnight = datetime(
            current_dt.year,
            current_dt.month,
            current_dt.day,
        ).astimezone()

        self.midnights = [local_midnight]

        for timezone in timezones:
            timezone_name = self._get_timezone_name(timezone)
            foreign_midnight = local_midnight.astimezone(
                pytz.timezone(timezone_name),
            )
            self.midnights.append(foreign_midnight)

    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.timezone_translations.get(timezone.lower())
        if timezone_name is None:
            raise SystemExit(f'error: {timezone !r} is not an available timezone')
        return timezone_name

    def _get_headers(self) -> List[str]:
        headers = []
        for idx, midnight in enumerate(self.midnights):
            header = str(midnight.tzinfo).upper() if idx else 'LOCAL'

            if self.zone:
                headers.append(f'{header} ({midnight.tzname()})')
            else:
                headers.append(header)

        return headers

    def _build_table(self) -> Table:
        headers = self._get_headers()
        table = Table()
        for header in headers:
            table.add_column(header, justify='center')

        fmt = '%Y-%m-%d %H:%M'

        current_hour = datetime.now().hour
        for hour in range(24):
            columns = [
                (midnight + timedelta(hours=hour)).strftime(fmt)
                for midnight in self.midnights
            ]
            if hour == current_hour:
                columns = [
                    f'[blue]{(midnight + timedelta(hours=hour)).strftime(fmt)}[/blue]'
                    for midnight in self.midnights
                ]

            table.add_row(*columns)

        return table

    def print_table(self) -> int:
        self._print_with_rich(self._build_table())
        return 0
