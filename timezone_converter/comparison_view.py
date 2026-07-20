"""Build and render the local-vs-foreign timezone comparison table."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone
from datetime import tzinfo
from difflib import get_close_matches
from typing import List
from typing import Optional
from zoneinfo import ZoneInfo

from rich.table import Table

from timezone_converter.helper import Helper


def _to_local(instant: datetime) -> datetime:
    # Single seam for the machine-local conversion. Production uses the
    # no-argument ``astimezone`` so it tracks DST; tests monkeypatch this to
    # pin a specific zone across platforms (``time.tzset`` is POSIX only).
    return instant.astimezone()


class ComparisonView(Helper):
    """Render a table comparing the local timezone against other zones.

    Rows are built from timezone-aware UTC instants spanning the local
    calendar day (23, 24, or 25 hours across a DST transition), so every
    column reflects the correct offset at each instant rather than a
    single frozen UTC offset.
    """

    def __init__(
        self,
        timezones: List[str],
        zone: bool,
        hour: Optional[int],
        order: bool,
    ) -> None:
        """Resolve the requested timezones and prepare the comparison state.

        Parameters
        ----------
        timezones : List[str]
            Foreign timezone names as given on the command line; each is
            resolved via
            :meth:`~timezone_converter.helper.Helper.resolve_timezone`.
        zone : bool
            If ``True``, include the resolved zone name (and current tz
            abbreviation) in each column header.
        hour : Optional[int]
            If given, restrict the table to this single hour (0-23)
            instead of the full local day.
        order : bool
            If ``True``, sort the foreign timezones by absolute offset
            from the local timezone.

        Raises
        ------
        SystemExit
            If a timezone name in `timezones` cannot be resolved.
        """
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
            self.zones.append(ZoneInfo(timezone_name))

        if order:
            self._sort_timezone_display()

    def _convert(
        self,
        zone: Optional[tzinfo],
        instant: Optional[datetime] = None,
    ) -> datetime:
        if instant is None:
            instant = self.base_instant
        return _to_local(instant) if zone is None else instant.astimezone(zone)

    def _offset(self, zone: Optional[tzinfo]) -> timedelta:
        # Aware datetimes always report an offset; ``or`` only narrows the type.
        return self._convert(zone).utcoffset() or timedelta(0)

    def _sort_timezone_display(self) -> None:
        local_offset = self._offset(None)
        self.zones.sort(key=lambda zone: abs(self._offset(zone) - local_offset))

    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.resolve_timezone(timezone)
        if timezone_name is None:
            error_msg = f'error: {timezone !r} is not an available timezone'
            possible_matches: List[str] = get_close_matches(
                timezone.lower(),
                self.searchable_timezones,
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

    def _day_instants(self) -> List[datetime]:
        # Walk the local day in real one-hour steps instead of a fixed 24, so
        # the LOCAL column always spans exactly one calendar day. A day is 23,
        # 24 or 25 hours long across DST changes; ``range(24)`` would otherwise
        # spill into the next day (spring forward) or drop the last hour (fall
        # back). Stepping absolute UTC instants keeps each conversion DST-aware.
        base_utc = self.base_instant.astimezone(datetime_timezone.utc)
        base_date = _to_local(self.base_instant).date()
        instants: List[datetime] = []
        hour = 0
        instant = base_utc
        while _to_local(instant).date() == base_date:
            instants.append(instant)
            hour += 1
            instant = base_utc + timedelta(hours=hour)
        return instants

    def _build_table(self) -> Table:
        headers = self._get_headers()
        table = Table()
        for header in headers:
            table.add_column(header, justify='center')

        if self.hour is not None:
            base_utc = self.base_instant.astimezone(datetime_timezone.utc)
            instants: List[datetime] = [base_utc + timedelta(hours=self.hour)]
        else:
            instants = self._day_instants()

        fmt = '%Y-%m-%d %H:%M'
        now = datetime.now().astimezone()
        for instant in instants:
            columns = [
                self._convert(zone, instant).strftime(fmt) for zone in self.zones
            ]
            highlighted = instant <= now < instant + timedelta(hours=1)
            style = 'blue' if highlighted else None
            table.add_row(*columns, style=style)

        return table

    def print_table(self) -> int:
        """Print the comparison table to the console.

        Returns
        -------
        int
            Always ``0``.
        """
        self._print_with_rich(self._build_table())
        return 0
