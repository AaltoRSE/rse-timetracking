import re

from .time import time_to_seconds

# List of KPIs and matching patterns.
KPI_defs = [
    dict(name='timesaved', type='time', tag='/timesaved'),
    dict(name='projects', type='int', tag='/projects'),
    dict(name='publications', type='int', tag='/publications'),
    dict(name='software', type='int', tag='/software'),
    dict(name='datasets', type='int', tag='/datasets'),
    dict(name='outputs', type='int', tag='/outputs'),

    # Deprecated, to be removed
    dict(name='publications', type='int', tag='publications'),
    dict(name='timesaved', type='time', tag='time saved'),
    dict(name='projects', type='int', tag='ongoing projects'),
    dict(name='outputs', type='int', tag='open outputs'),
    dict(name='outputs', type='int', tag='/openoutputs'),
]


def parse_KPIs(content):
    """Match the note body against all KPIs defined above."""
    content = content.lower()

    for line in content.split('\n'):

      for kpi in KPI_defs:
        if not line.startswith(kpi['tag']):
            continue

        # We found a matching KPI!
        _, value_string = line.split(kpi['tag'], 1)

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
        yield kpi['name'], value
