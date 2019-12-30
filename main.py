"""\
I'm annoyed with the usual webpages that convert timezones
but only show ONE hour at a time, so i created this script
to have a simple and quick way of comparing timezones.
"""

import datetime
import sys

import pytz

from timezones import alias


def get_date():
    today = datetime.datetime.now().astimezone()
    year, month, day = [int(i) for i in str(today).split(' ')[0].split('-')]

    return year, month, day


def humanify(local, foreign):
    local_splitted = str(local).split(' ')
    local_date = "-".join(local_splitted[0].split('-'))
    local_time = ":".join(local_splitted[1].split(':')[:2])
    local_string = " ".join([local_date, local_time])

    foreign_splitted = str(foreign).split(' ')
    foreign_date = "-".join(foreign_splitted[0].split('-'))
    foreign_time = ":".join(foreign_splitted[1].split(':')[:2])
    foreign_string = " ".join([foreign_date, foreign_time])

    return local_string, foreign_string


def print_list(local, foreign, length):
    print("LOCAL".center(length), city.upper().center(length))

    for i in range(24):
        local_plus = local + datetime.timedelta(hours=i)
        foreign_plus = foreign + datetime.timedelta(hours=i)

        local_string, foreign_string = humanify(local_plus, foreign_plus)
        local_time = local_string.split(' ')[1]
        foreign_time = foreign_string.split(' ')[1]

        print(local_time.center(length), foreign_time.center(length))


def print_list_complete(local, foreign, length):
    print("LOCAL".center(length), city.upper().center(length))

    for i in range(24):
        local_plus = local + datetime.timedelta(hours=i)
        foreign_plus = foreign + datetime.timedelta(hours=i)

        local_string, foreign_string = humanify(local_plus, foreign_plus)

        print(local_string.center(length), foreign_string.center(length))


try:
    city = sys.argv[1].lower()
    tz = alias[city]
except IndexError:
    print("Error: City not provided")
except KeyError:
    print("Error: City not found")
else:
    # Get current date and time
    year, month, day = get_date()

    # Get local datetime object of today at 00:00
    local = datetime.datetime(year=year, month=month, day=day).astimezone()

    # Get foreign datetime object of today at 00:00
    foreign = local.astimezone(pytz.timezone(tz))

    # Get length of local date for output formatting
    length = len(str(local).split('+')[0])

    # Print full table with dates
    print_list_complete(local, foreign, length)

    # Print simplified table with only hours
    print_list(local, foreign, len(city))


# TODO: option to display date (2019-12-30 00:00:00, 2019-12-29 18:00:00)
# TODO: option to display timezone (00:00:00+01:00, 18:00:00-05:00)
# TODO: color code
# TODO: add argument parsing
# TODO: add verbose
# TODO: document functions
# TODO: improve error handling
