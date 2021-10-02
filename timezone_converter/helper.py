from typing import Union

import pytz
from rich.columns import Columns
from rich.console import Console
from rich.table import Table


class Helper:
    timezone_translations = {tz.lower().split('/')[-1]: tz for tz in pytz.all_timezones}

    @staticmethod
    def _print_with_rich(obj: Union[str, Columns, Table]) -> None:
        Console().print(obj)
