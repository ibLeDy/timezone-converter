import datetime
from argparse import ArgumentParser

import pytz


def display_timezones(local, foreign, capital):
    fmt = '%Y-%m-%d %H:%M'
    length = len(local.strftime(fmt)) + 3

    local_header = 'LOCAL'
    foreign_header = f'{capital.upper()}'
    print(local_header.center(length), foreign_header.center(length))

    for hour in range(24):
        local_plus = (local + datetime.timedelta(hours=hour)).strftime(fmt)
        foreign_plus = (foreign + datetime.timedelta(hours=hour)).strftime(fmt)
        print(local_plus.center(length), foreign_plus.center(length))


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Compare your local timezone with a foreign one'
    )
    parser.add_argument(
        'timezone',
        help='foreign timezone that gets compared with your local one',
    )

    args = parser.parse_args()
    timezones = {tz.lower().split('/')[-1]: tz for tz in pytz.all_timezones}

    try:
        timezone = timezones[args.timezone]
    except KeyError:
        raise Exception(f'{args.timezone !r} is not an available timezone')

    today = datetime.datetime.now()
    local_midnight = datetime.datetime(
        today.year, today.month, today.day
    ).astimezone()
    foreign_midnight = local_midnight.astimezone(pytz.timezone(timezone))
    display_timezones(local_midnight, foreign_midnight, args.timezone)
