import re

# Regular expression matching lines such as:
# added 1h 13m 48s of time spent at 2020-11-04
time_spent_pattern = re.compile(r'^(added|subtracted) ((?:\d+[a-z]{1,2} ?)+) of time spent at (\d{4}-\d{2}-\d{2})$')  # noqa

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
    mo=4 * 5 * 8 * 60 * 60,
    # Now the other, one-letter, postfixes:
    w=5 * 8 * 60 * 60,
    d=8 * 60 * 60,
    h=60 * 60,
    m=60,
    s=1,
)


def parse_time_spent(content):
    """Parse the time tracking information from a note body."""
    m = time_spent_pattern.match(content)
    if m is None:
        return None  # Note did not contain time tracking information

    # The capture groups of the regex split the note into useful components
    added_or_subtracted, time_spent_string, date_added = m.groups()
    return time_spent_string, added_or_subtracted


def time_to_seconds(time_string, added_or_subtracted='added'):
    """Parse a time string to an int number of seconds."""
    if time_string is None:  # Parse_time returns None if there is no match.
        return  # No match, return None

    time_spent = 0  # In seconds

    # Parse each unit (e.g. "24d") into an integer number of seconds
    for unit in time_string.split(' '):
        for postfix, multiplier in postfixes.items():
            if unit.endswith(postfix):
                time_spent += int(unit[:-len(postfix)]) * multiplier
                break
        else:  # No postfix matched
            raise RuntimeError(f'Could not parse {unit}')

    if added_or_subtracted == 'subtracted':
        time_spent = -time_spent

    return time_spent
