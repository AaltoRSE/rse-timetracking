import re

from .time import time_to_seconds

# List of KPIs and matching patterns.
KPI_defs = [
    dict(name='Researcher time saved', type='time', tag='time saved'),
    dict(name='Projects supported', type='int', tag='ongoing projects'),
    dict(name='Publications supported', type='int', tag='publications'),
    dict(name='Open outputs', type='int', tag='open outputs'),
]


def parse_KPIs(content):
    """Match the note body against all KPIs defined above."""
    content = content.lower()

    for kpi in KPI_defs:
        if not content.startswith(kpi['tag']):
            continue

        # We found a matching KPI!
        _, value_string = content.split(kpi['tag'], 1)

        # You can write KPIs as:
        #     'publications 1'
        # or
        #     'publications: 1'
        if value_string.startswith(':'):
            _, value_string = value_string.split(':', 1)

        # Interpret time string as number of seconds
        if kpi['type'] == 'time':
            value = time_to_seconds(value_string.strip())
        # Interpred the number as integer
        elif kpi['type'] == 'int':
            value = int(value_string.strip())
        else:
            raise TypeError(f'Invalid type for KPI: {kpi["type"]}')

        # Return a tuple with the KPI name and the value.
        # Since we return here, a note can only match one KPI.
        return kpi['name'], value
    return None
