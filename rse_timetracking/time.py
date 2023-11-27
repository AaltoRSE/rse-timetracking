import math
import re

import pytest

# Regular expression matching lines such as:
# added 1h 13m 48s of time spent at 2020-11-04
time_spent_pattern = re.compile(r'^(added|subtracted) ((?:\d+[a-z]{1,2} ?)+) of time spent(?: at (\d{4}-\d{2}-\d{2}))?$')  # noqa

time_record_pattern = re.compile(r'([0-9.-] *[a-z]{1,2})', re.I)

# Time can we denoted as "1mo 2d 6h" and so forth. Each postfix means a certain
# number of seconds.
#
# From https://docs.gitlab.com/ee/user/project/time_tracking.html
#
# Months (mo)
# Weeks (w)
# Days (d)
# Hours (h)
# Minutes (m)
#
# Default conversion rates are 1mo = 4w, 1w = 5d and 1d = 8h
postfixes = dict(
    # NOTE: This postfix is two letters and hence should be matched first!
    mo=60 * 60 * 8 * 5 * 4,
    # Now the other, one-letter, postfixes:
    w= 60 * 60 * 8 * 5,
    d= 60 * 60 * 8,
    h= 60 * 60,
    m= 60,
    s= 1,
)
valid_units = ' '.join(sorted(postfixes.keys()))


def parse_time_spent(content):
    """Parse the time tracking information from a note body."""
    m = time_spent_pattern.match(content)
    if m is None:
        return None  # Note did not contain time tracking information

    # The capture groups of the regex split the note into useful components
    added_or_subtracted, time_spent_string, date_added = m.groups()
    return time_spent_string, added_or_subtracted, date_added


def time_to_seconds(time_string, added_or_subtracted='added'):
    """Parse a time string to an int number of seconds."""
    if time_string is None:  # Parse_time returns None if there is no match.
        return  # No match, return None

    time_spent = 0  # In seconds

    # Parse each unit (e.g. "24d") into an integer number of seconds
    records = time_record_pattern.findall(time_string)
    if not records:
        raise RuntimeError(f'Could not parse anything times from "{time_string}"')
    for unit in records:
        for postfix, multiplier in postfixes.items():
            if unit.endswith(postfix):
                time_spent += float(unit[:-len(postfix)]) * multiplier
                break

        else:  # No postfix matched
            raise RuntimeError(f'Could not parse "{unit}" in time string "{time_string}" (valid units are {valid_units})')

    if added_or_subtracted == 'subtracted':
        time_spent = -time_spent

    return int(time_spent)


def human_time(seconds, rounding=None):
    """Convert a number of seconds to a human time.

    rounding: round to this many seconds before converting.

    The output format is not stable
    """
    if seconds is None or math.isnan(seconds):
        return None
    if rounding:
        seconds = int(rounding * round(seconds/rounding))
    result = [ ]
    for suffix, period in postfixes.items():
        if seconds >= period:
            result.append(f"{seconds//period}{suffix}")
            seconds = seconds % period
    return ''.join(result)

def test_human_time():
    assert human_time(2)  == '2s'
    assert human_time(62) == '1m2s'
    assert human_time(3662) == '1h1m2s'
    assert human_time(1*postfixes['mo'] + 3662) == '1mo1h1m2s'
    # with rounding
    assert human_time(3662, rounding=3600) == '1h'
    assert human_time(3550, rounding=3600) == '1h'
    assert human_time(1*postfixes['mo'] + 3662, rounding=3600) == '1mo1h'

def test_time_to_seconds():
    assert time_to_seconds('2s') == 2
    assert time_to_seconds('2m') == 120
    assert time_to_seconds('2h') == 7200
    assert time_to_seconds('2d') == 2 * postfixes['d']
    assert time_to_seconds('2w') == 2 * postfixes['w']
    assert time_to_seconds('2mo') == 2 * postfixes['mo']

    assert time_to_seconds('2m2s') == 122
    assert time_to_seconds('2m 2s') == 122
    assert time_to_seconds('2m2mo') == 2 * postfixes['mo'] + 120
    assert time_to_seconds('2mo 2m') == 2 * postfixes['mo'] + 120

    with pytest.raises(RuntimeError, match='Could not parse "2x"'):
        time_to_seconds('2x')
    with pytest.raises(RuntimeError, match='Could not parse anything'):
        time_to_seconds('')
