from datetime import datetime
from datetime import timedelta
from datetime import tzinfo
from difflib import get_close_matches
from typing import Iterable
from typing import List
from typing import Optional

import pytz
from rich.table import Table

from timezone_converter.helper import Helper


class ComparisonView(Helper):
    def __init__(
        self,
        timezones: List[str],
        zone: bool,
        hour: Optional[int],
        order: bool,
    ) -> None:
        self.zone = zone
        self.hour = hour

        current_dt = datetime.now()
        self.base_instant = datetime(
            current_dt.year,
            current_dt.month,
            current_dt.day,
        ).astimezone()

        # ``None`` represents the local timezone; it is rendered with the
        # no-argument ``astimezone`` so it tracks DST at each instant.
        self.zones: List[Optional[tzinfo]] = [None]

        for timezone in timezones:
            timezone_name = self._get_timezone_name(timezone)
            self.zones.append(pytz.timezone(timezone_name))

        if order:
            self._sort_timezone_display()

    def _convert(
        self,
        zone: Optional[tzinfo],
        instant: Optional[datetime] = None,
    ) -> datetime:
        if instant is None:
            instant = self.base_instant
        return instant.astimezone() if zone is None else instant.astimezone(zone)

    def _offset(self, zone: Optional[tzinfo]) -> timedelta:
        # Aware datetimes always report an offset; ``or`` only narrows the type.
        return self._convert(zone).utcoffset() or timedelta(0)

    def _sort_timezone_display(self) -> None:
        local_offset = self._offset(None)
        self.zones.sort(key=lambda zone: abs(self._offset(zone) - local_offset))

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
        for zone in self.zones:
            header = 'LOCAL' if zone is None else str(zone).upper()

            if self.zone:
                headers.append(f'{header} ({self._convert(zone).tzname()})')
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
        now = datetime.now().astimezone()
        for hour in hours_to_print:
            instant = self.base_instant + timedelta(hours=hour)
            columns = [
                self._convert(zone, instant).strftime(fmt) for zone in self.zones
            ]
            highlighted = instant <= now < instant + timedelta(hours=1)
            style = 'blue' if highlighted else None
            table.add_row(*columns, style=style)

        return table

    def print_table(self) -> int:
        self._print_with_rich(self._build_table())
        return 0
