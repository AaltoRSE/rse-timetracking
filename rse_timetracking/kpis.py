import re

from .time import time_to_seconds

LIST_SPLIT = re.compile(', *')

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

Metadata_defs = [
    dict(name='contact', type='list', tag=re.compile('/contacts?')),
    dict(name='supervisor', type='list', tag=re.compile('/supervisors?')),
    dict(name='summary', type='str', tag='/summary'),
    ]


def parse_KPIs(content, defs=KPI_defs):
    """Match the note body against all KPIs defined above."""

    for line in content.split('\n'):

      for kpi in defs:
        if isinstance(kpi['tag'], re.Pattern):
            m = kpi['tag'].match(line)
            if not m:
                continue
            _, value_string = kpi['tag'].split(line, maxsplit=1)
        else:
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
            try:
                value = time_to_seconds(value_string.strip())
            except ValueError as e:
                print(e.__dict__)
                raise ValueError(str(e) + f'at "{line}"')
        # Interpred the number as integer
        elif kpi['type'] == 'int':
            value = int(value_string.strip())
        # string
        elif kpi['type'] == 'str':
            value = value_string.strip()
        # list
        elif kpi['type'] == 'list':
            values = LIST_SPLIT.split(value_string)
            for value in values:
                #print(kpi['name'], value.strip())
                yield kpi['name'], value.strip()
            continue

        else:
            raise TypeError(f'Invalid type for KPI: {kpi["type"]}')

        # Return a tuple with the KPI name and the value.
        #print(kpi['name'], value)
        yield kpi['name'], value
