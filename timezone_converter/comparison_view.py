import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone
from datetime import tzinfo
from difflib import get_close_matches
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from zoneinfo import ZoneInfo

from rich.table import Table

from timezone_converter.helper import Helper
from timezone_converter.helper import local_timezone

# ``--hour`` without a value means "the current hour", but which hour that is
# depends on the local zone, and the parser runs before ``--local`` or ``TZ``
# has been resolved. It passes this marker instead and the view fills in the
# hour once the zone is known. ``-1`` can never come from the user, since
# ``--hour`` rejects anything outside 0-23.
CURRENT_HOUR = -1


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
        difference: bool,
        day: Optional[date] = None,
        local: Optional[str] = None,
        output_format: str = 'table',
        highlight: Optional[Tuple[int, Optional[str]]] = None,
        span: Optional[int] = None,
        hour_range: Optional[Tuple[int, int, Optional[str]]] = None,
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
            If given, restrict the table to this local wall-clock hour
            (0-23) instead of the full local day. :data:`CURRENT_HOUR` means
            the current hour in the local zone.
        order : bool
            If ``True``, sort the foreign timezones by absolute offset
            from the local timezone.
        difference : bool
            If ``True``, append each foreign column's signed hour offset
            from the local timezone to the header (e.g. ``+5h``).
        day : Optional[date]
            The local calendar day to compare. Defaults to today.
        local : Optional[str]
            Timezone to treat as local, overriding the machine's own. Given
            in the same forms as `timezones`.
        output_format : str
            ``'table'`` for the Rich table, or ``'json'`` for a
            machine-readable payload on stdout.
        highlight : Optional[Tuple[int, Optional[str]]]
            An hour (0-23) to highlight instead of the current one, and the
            timezone whose hour it is: ``None`` for the local column,
            otherwise one of `timezones` (or `local`).
        span : Optional[int]
            If given, show only this many hours, starting at the highlighted
            hour, or ending at it if negative. The highlighted hour defaults
            to the current one.
        hour_range : Optional[Tuple[int, int, Optional[str]]]
            If given, show only the hours from the first through the second,
            wrapping past midnight when the second is smaller, read in the
            given timezone (``None`` for the local column).

        Raises
        ------
        SystemExit
            If a timezone name in `timezones`, `local`, `highlight` or
            `hour_range` cannot be resolved, if a `highlight` or `hour_range`
            timezone is not one of the compared ones, or if an hour they name
            never falls on the local day.
        """
        self.zone = zone
        self.hour = hour
        self.difference = difference
        self.output_format = output_format

        # ``None`` keeps the machine's own timezone, tracked through
        # ``_to_local``. An override is resolved the same way a foreign zone
        # is, so a typo gets the same suggestions and the same exit code.
        self.local_zone: Optional[tzinfo] = None
        if local is not None:
            self.local_zone = ZoneInfo(self._get_timezone_name(local))
        else:
            # Without --local, ``TZ`` names the local zone when it holds an IANA
            # name, which is how a container is usually told its timezone.
            # Resolving it here, rather than leaving it to the C library behind
            # ``astimezone``, keeps it working on images without the OS
            # timezone database; see ``helper.local_timezone``.
            self.local_zone = local_timezone()

        # Local midnight of the day being compared, in whichever zone counts
        # as local. For the machine's own zone, ``astimezone`` on a naive
        # datetime resolves it against the rules in force on that date, so a
        # past or future day gets that day's offset rather than today's.
        chosen_day = day if day is not None else self._today()
        naive_midnight = datetime(
            chosen_day.year,
            chosen_day.month,
            chosen_day.day,
        )
        if self.local_zone is None:
            self.base_instant = naive_midnight.astimezone()
        else:
            self.base_instant = naive_midnight.replace(tzinfo=self.local_zone)

        if self.hour == CURRENT_HOUR:
            now = datetime.now(datetime_timezone.utc)
            self.hour = self._to_local(now).hour

        # ``None`` represents the local column; it is rendered through
        # ``_to_local`` so it tracks DST at each instant, whether that means
        # the machine's zone or the ``--local`` override.
        self.zones: List[Optional[tzinfo]] = [None]

        for timezone in timezones:
            timezone_name = self._get_timezone_name(timezone)
            self.zones.append(ZoneInfo(timezone_name))

        if order:
            self._sort_timezone_display()

        # The hour to highlight, and the column it is read in (``None`` is the
        # local column). Without --highlight it stays ``None`` and the current
        # hour is highlighted, except under --span, which needs an hour to
        # anchor on and takes the current one, like a bare --hour does.
        self.span = span
        self.highlight_hour: Optional[int] = None
        self.highlight_zone: Optional[tzinfo] = None
        if highlight is not None:
            self.highlight_hour, highlight_name = highlight
            if highlight_name is not None:
                self.highlight_zone = self._column_zone(highlight_name, '--highlight')
        elif span is not None:
            now = datetime.now(datetime_timezone.utc)
            self.highlight_hour = self._to_local(now).hour

        # The hours --range bounds the table with, and the column they are
        # read in (``None`` is the local column).
        self.hour_range: Optional[Tuple[int, int]] = None
        self.range_zone: Optional[tzinfo] = None
        if hour_range is not None:
            start, end, range_name = hour_range
            self.hour_range = (start, end)
            if range_name is not None:
                self.range_zone = self._column_zone(range_name, '--range')

    def _column_zone(self, name: str, flag: str) -> Optional[tzinfo]:
        # ``17@tokyo`` reads 17h in the Tokyo column, so Tokyo has to be one.
        # ``resolve_timezone`` first, so a name already given as a column
        # does not print its ambiguity warning a second time; an unknown
        # name still gets the usual error and suggestions.
        resolved = self.resolve_timezone(name) or self._get_timezone_name(name)
        if self.local_zone is not None and str(self.local_zone) == resolved:
            return None
        for zone in self.zones:
            if zone is not None and str(zone) == resolved:
                return zone
        self._print_error_with_rich(
            f'error: {name!r} is not one of the compared timezones; add it as '
            f'a timezone argument to use it with {flag}',
        )
        raise SystemExit(1)

    def _today(self) -> date:
        # "Today" is a local notion, so an overridden local zone decides it
        # too: on a UTC host comparing against Europe/Madrid, the day to show
        # is Madrid's, which is the point of the override.
        if self.local_zone is None:
            return datetime.now().date()
        return datetime.now(self.local_zone).date()

    def _to_local(self, instant: datetime) -> datetime:
        # Routes every "what does this instant look like locally" question
        # through one place, so the override applies to the LOCAL column, to
        # the day boundaries and to wall-clock hour selection alike.
        if self.local_zone is None:
            return _to_local(instant)
        return instant.astimezone(self.local_zone)

    def _convert(
        self,
        zone: Optional[tzinfo],
        instant: Optional[datetime] = None,
    ) -> datetime:
        if instant is None:
            instant = self.base_instant
        return self._to_local(instant) if zone is None else instant.astimezone(zone)

    def _offset(self, zone: Optional[tzinfo]) -> timedelta:
        # Aware datetimes always report an offset; ``or`` only narrows the type.
        return self._convert(zone).utcoffset() or timedelta(0)

    def _sort_timezone_display(self) -> None:
        local_offset = self._offset(None)
        self.zones.sort(key=lambda zone: abs(self._offset(zone) - local_offset))

    def _get_timezone_name(self, timezone: str) -> str:
        timezone_name = self.resolve_timezone(timezone)
        if timezone_name is None:
            # One shape for every failure here: the message always goes
            # through Rich on stderr, and the exit is always ``SystemExit(1)``.
            # ``SystemExit(str)`` would print the message itself and exit 1 as
            # well, but bypasses Rich and leaves two different code paths for
            # what is one error.
            error_msg = f'error: {timezone !r} is not an available timezone'
            self._print_error_with_rich(error_msg)
            possible_matches: List[str] = get_close_matches(
                timezone.lower(),
                self.searchable_timezones,
                n=5,
            )
            if possible_matches:
                table = Table()
                table.add_column('Closest matches')
                for match in possible_matches:
                    table.add_row(match)
                self._print_error_with_rich(table)
            raise SystemExit(1)

        # A short name that several zones share resolves to exactly one of
        # them, and which one is an implementation detail of the lookup
        # table. Say so, on stderr so it cannot pollute piped output, rather
        # than letting the wrong city look like the right answer.
        alternatives = self.ambiguous_alternatives(timezone)
        if alternatives:
            others = ', '.join(name for name in alternatives if name != timezone_name)
            self._print_error_with_rich(
                f'warning: {timezone !r} matches {len(alternatives)} timezones; '
                f'using {timezone_name !r}. Give a full path for: {others}',
            )
        return timezone_name

    def _difference_hours(self, zone: Optional[tzinfo]) -> float:
        # Signed hours relative to the local offset, evaluated at the same
        # ``base_instant`` used for ``--zone``'s tzname, so the two flags stay
        # consistent across DST transitions. The table and the JSON payload
        # both read this, so there is one definition of the difference.
        return (self._offset(zone) - self._offset(None)).total_seconds() / 3600

    def _format_difference(self, zone: Optional[tzinfo]) -> str:
        # Zero-pad the decimal only when the difference is not a whole number
        # (e.g. ``+9.5h`` but ``-5h``, never ``-5.0h``) to keep the format
        # compact and predictable.
        diff_hours = self._difference_hours(zone)
        if diff_hours.is_integer():
            return f'{diff_hours:+.0f}h'
        formatted = f'{diff_hours:+.2f}'.rstrip('0').rstrip('.')
        return f'{formatted}h'

    def _get_headers(self) -> List[str]:
        headers: List[str] = []
        for zone in self.zones:
            header = 'LOCAL' if zone is None else str(zone).upper()

            if self.zone:
                header = f'{header} ({self._convert(zone).tzname()})'

            if self.difference and zone is not None:
                header = f'{header} {self._format_difference(zone)}'

            headers.append(header)

        return headers

    def _day_instants(self) -> List[datetime]:
        # Walk the local day in real one-hour steps instead of a fixed 24, so
        # the LOCAL column always spans exactly one calendar day. A day is 23,
        # 24 or 25 hours long across DST changes; ``range(24)`` would otherwise
        # spill into the next day (spring forward) or drop the last hour (fall
        # back). Stepping absolute UTC instants keeps each conversion DST-aware.
        base_utc = self.base_instant.astimezone(datetime_timezone.utc)
        base_date = self._to_local(self.base_instant).date()
        instants: List[datetime] = []
        hour = 0
        instant = base_utc
        while self._to_local(instant).date() == base_date:
            instants.append(instant)
            hour += 1
            instant = base_utc + timedelta(hours=hour)
        return instants

    def _hour_in(self, zone: Optional[tzinfo], instant: datetime) -> int:
        # The hour a column reads at ``instant``. Reading it off the rendered
        # time, rather than matching a whole hour, also covers zones on a half
        # or quarter hour: in Asia/Kolkata the 17h row reads 17:30.
        return self._convert(zone, instant).hour

    def _is_highlighted(self, instant: datetime, now: datetime) -> bool:
        # The row that starts at ``instant`` is highlighted when it contains
        # ``now``, or with --highlight when the chosen column reads the chosen
        # hour.
        if self.highlight_hour is None:
            return instant <= now < instant + timedelta(hours=1)
        return self._hour_in(self.highlight_zone, instant) == self.highlight_hour

    def _missing_hour(self, hour: int, zone: Optional[tzinfo]) -> SystemExit:
        # Only a DST transition can make an hour miss a local day, whose 23 to
        # 25 real hours otherwise pass through every hour of every zone.
        where = 'in your local timezone' if zone is None else f'in {zone}'
        self._print_error_with_rich(
            f'error: {hour:02d}:00 {where} never falls on '
            f'{self._to_local(self.base_instant).date()} in your local '
            'timezone, a clock change skips over it',
        )
        return SystemExit(1)

    def _span_instants(
        self,
        instants: List[datetime],
        span: int,
        hour: int,
    ) -> List[datetime]:
        # Anchor on the first row of the local day where the highlighted column
        # reads ``hour``, then step real hours from it, so a window across a
        # DST change shows the hours that actually happen. A fall-back day
        # repeats an hour; the first one wins.
        anchors = [
            instant
            for instant in instants
            if self._hour_in(self.highlight_zone, instant) == hour
        ]
        if not anchors:
            raise self._missing_hour(hour, self.highlight_zone)
        # ``span`` counts the hours shown, the anchor included: +8 is the
        # anchor and the 7 after it, -8 the 7 before it and the anchor.
        offsets = range(span) if span > 0 else range(span + 1, 1)
        return [anchors[0] + timedelta(hours=offset) for offset in offsets]

    def _range_instants(
        self,
        instants: List[datetime],
        start: int,
        end: int,
    ) -> List[datetime]:
        # From the first ``start`` row of the local day, step real hours until
        # the column reads ``end``, so 22-06 runs past midnight and a range
        # across a DST change neither gains nor loses an hour at its end.
        first = [
            instant
            for instant in instants
            if self._hour_in(self.range_zone, instant) == start
        ]
        if not first:
            raise self._missing_hour(start, self.range_zone)
        # 10-22 is 12 hours on the clock. A clock change can make that one
        # real hour more or less, never more, so ``end`` is searched for only
        # that far: if a spring-forward skips it, looking further would find
        # the next day's instead and quietly run the table past it.
        clock_hours = (end - start) % 24
        rows = []
        instant = first[0]
        for _ in range(clock_hours + 2):
            rows.append(instant)
            if self._hour_in(self.range_zone, instant) == end:
                return rows
            instant += timedelta(hours=1)
        raise self._missing_hour(end, self.range_zone)

    def _selected_instants(self) -> List[datetime]:
        # ``--hour N`` means "the local wall-clock hour N", which is not the
        # same as "N real hours after local midnight". On a spring-forward day
        # those drift apart by an hour for every hour past the transition, and
        # on a fall-back day they drift the other way, so the hour has to be
        # picked out of the real local day rather than computed by arithmetic.
        instants = self._day_instants()
        if self.hour is None:
            # --span always has an hour to anchor on: --highlight's, or the
            # current one the constructor filled in.
            if self.span is not None and self.highlight_hour is not None:
                return self._span_instants(instants, self.span, self.highlight_hour)
            if self.hour_range is not None:
                return self._range_instants(instants, *self.hour_range)
            if self.highlight_hour is not None:
                now = datetime.now().astimezone()
                if not any(self._is_highlighted(instant, now) for instant in instants):
                    raise self._missing_hour(self.highlight_hour, self.highlight_zone)
            return instants

        # A fall-back day repeats a local hour, so this can legitimately match
        # twice; both instants are shown, matching the full-day table.
        matching = [
            instant for instant in instants if self._to_local(instant).hour == self.hour
        ]
        if not matching:
            # A spring-forward day skips a local hour entirely; there is no
            # instant to show, so say so instead of rendering an empty table.
            self._print_error_with_rich(
                f'error: {self.hour:02d}:00 does not exist on '
                f'{self._to_local(self.base_instant).date()} in your local '
                'timezone, '
                'the clocks skip forward over it',
            )
            raise SystemExit(1)
        return matching

    def _build_table(self) -> Table:
        headers = self._get_headers()
        table = Table()
        for header in headers:
            table.add_column(header, justify='center')

        instants = self._selected_instants()

        fmt = '%Y-%m-%d %H:%M'
        now = datetime.now().astimezone()
        for instant in instants:
            columns = [
                self._convert(zone, instant).strftime(fmt) for zone in self.zones
            ]
            style = 'blue' if self._is_highlighted(instant, now) else None
            table.add_row(*columns, style=style)

        return table

    def _zone_name(self, zone: Optional[tzinfo]) -> Optional[str]:
        # The IANA name, where there is one to report. The machine's own zone
        # is reached through ``astimezone()``, which yields a fixed-offset
        # tzinfo rather than a named zone, so ``null`` is the honest answer
        # there instead of an abbreviation masquerading as a zone name.
        if zone is not None:
            return str(zone)
        return None if self.local_zone is None else str(self.local_zone)

    def _build_payload(self) -> Dict[str, Any]:
        instants = self._selected_instants()
        now = datetime.now().astimezone()
        return {
            'date': self._to_local(self.base_instant).date().isoformat(),
            'columns': [
                {
                    'label': 'LOCAL' if zone is None else str(zone).upper(),
                    'zone': self._zone_name(zone),
                    'abbreviation': self._convert(zone).tzname(),
                    'difference_hours': self._difference_hours(zone),
                }
                for zone in self.zones
            ],
            'rows': [
                {
                    'current': instant <= now < instant + timedelta(hours=1),
                    # What the table shows in blue: the current hour, or the
                    # one --highlight picked.
                    'highlighted': self._is_highlighted(instant, now),
                    # ISO-8601 with the offset, unlike the table's display
                    # format: a consumer needs the offset to know which
                    # instant a repeated fall-back hour refers to.
                    'times': [
                        self._convert(zone, instant).isoformat() for zone in self.zones
                    ],
                }
                for instant in instants
            ],
        }

    def print_table(self) -> int:
        """Print the comparison to the console.

        Renders the Rich table, or the JSON payload when the view was
        built with ``output_format='json'``.

        Returns
        -------
        int
            Always ``0``.
        """
        if self.output_format == 'json':
            # Deliberately not routed through Rich: its wrapping and
            # highlighting would corrupt output whose whole purpose is to be
            # parsed by something else.
            self._print_plain(json.dumps(self._build_payload(), indent=2))
            return 0

        self._print_with_rich(self._build_table())
        return 0
