from datetime import datetime
from datetime import timedelta
from difflib import get_close_matches
from typing import Iterable
from typing import List
from typing import Union

import pytz
from rich.table import Table

from timezone_converter.helper import Helper


class ComparisonView(Helper):
    def __init__(
        self,
        timezones: List[str],
        zone: bool,
        hour: Union[int, None],
        order: bool,
    ) -> None:
        self.zone = zone
        self.hour = hour

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

        if order:
            self._sort_timezone_display()

    def _sort_timezone_display(self) -> None:
        local_offset = int(self.midnights[0].strftime('%z'))
        self.midnights.sort(
            key=lambda zone: abs(local_offset - int(zone.strftime('%z'))),
        )

    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.timezone_translations.get(timezone.lower())
        if timezone_name is None:
            error_msg = f'error: {timezone !r} is not an available timezone'
            possible_matches: List[str] = get_close_matches(
                timezone,
                self.timezone_translations,
                n=5,
            )
            if len(possible_matches) == 0:
                raise SystemExit(error_msg)
            table = Table()
            table.add_column('Closest matches')
            for match in possible_matches:
                table.add_row(match)
            self._print_with_rich(error_msg)
            self._print_with_rich(table)
            raise SystemExit(1)
        return timezone_name

    def _get_headers(self) -> List[str]:
        headers: List[str] = []
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

        hours_to_print: Iterable[int] = range(24)
        if self.hour is not None:
            hours_to_print = [self.hour]

        fmt = '%Y-%m-%d %H:%M'
        current_hour = datetime.now().hour
        for hour in hours_to_print:
            columns = [
                (midnight + timedelta(hours=hour)).strftime(fmt)
                for midnight in self.midnights
            ]
            style = 'blue' if hour == current_hour else None
            table.add_row(*columns, style=style)

        return table

    def print_table(self) -> int:
        self._print_with_rich(self._build_table())
        return 0
