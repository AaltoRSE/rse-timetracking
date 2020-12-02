import re

from .time import time_to_seconds

# List of KPIs and matching patterns.
KPI_defs = [
    dict(name="Researcher time saved", type="time",
         pat=re.compile(r'(T|t)ime saved ((?:\d+[a-z]{1,2} ?)+)')),
    dict(name="Projects supported", type="int",
         pat=re.compile(r'(O|o)ngoing projects \?:\d')),
    dict(name="Publications supported", type="int",
         pat=re.compile(r'(P|p)ublications \?:\d')),
    dict(name="Open outputs", type="int",
         pat=re.compile(r'(O|o)pen outputs \?:\d')),
]


def parse_KPIs(content, verbose=False):
    """Match the note body against all KPIs defined above."""
    for kpi in KPI_defs:
        m = kpi['pat'].match(content)
        if m is None:
            continue  # Note did not match the regular expression

        # The capture groups of the regex split the note into useful
        # components. The second group contains the number we need.
        _, value_string = m.groups()

        # Interpret time string as number of seconds
        if kpi['type'] == 'time':
            value = time_to_seconds(value_string)
        # Interpred the number as integer
        elif kpi['type'] == 'int':
            value = int(value_string)
        else:
            raise TypeError(f'Invalid type for KPI: {kpi["type"]}')

        # Return a tuple with the KPI name and the value.
        # Since we return here, a note can only match one KPI.
        return kpi['name'], value
    return None, None
