"""
Scrape version.aalto.fi to assemble statistics about RSE projects. For each
project, Key Performance Indicators (KPIs) are gathered from the issue tracker.
"""
import sys
from collections import defaultdict
from datetime import timedelta
import dateutil
import itertools
import pickle
import statistics

import pytz
import gitlab

from .time import time_to_seconds, parse_time_spent
from . import kpis
from .objects import Project

TZ = pytz.timezone('Europe/Helsinki')


def parse_body(p, body, created_at=None):
    # Check KPIs
    for KPI_parts in kpis.parse_KPIs(body):
        KPI_name, KPI_value = KPI_parts
        p.kpi_list.append(
            (KPI_name, KPI_value, created_at)
            )

    # Check metadata
    for KPI_parts in kpis.parse_KPIs(body, defs=kpis.Metadata_defs):
        KPI_name, KPI_value = KPI_parts
        p.metadata_list.append(
            (KPI_name, KPI_value, created_at)
            )



def scrape2(args):
    """Main function that serves as the entrypoint to rse_timetracking."""

    # Try to connect to gitlab
    gitlab_cfg_msg = """
    Could not connect to Gitlab.

    To use the Gitlab API, we need login information. Since this is sensitive
    we're not putting it in this script. Instead, you are asked to create a
    file .python-gitlab.cfg in your home directory with the following contents:

    [aalto]
    url = https://version.aalto.fi/gitlab
    private_token = <your_private_token>

    You can obtain a private token by going to your user settings in GitLab and
    then go to the "Access Tokens" section. For this scraper script, the token
    only needs access to the API and reading the repo.
    """
    try:
        gl = gitlab.Gitlab.from_config('aalto')
    except gitlab.config.ConfigError as err:
        sys.exit(f'{gitlab_cfg_msg}\n'
                 f'The error message that was raised was: {err}')

    try:
        gl.auth()
    except gitlab.GitlabAuthenticationError as err:
        sys.exit(f'Could not login to {gl.url}. Are you sure the access token '
                 f'is correct?\nThe error message that was raised was: {err}')

    # Find the correct repo
    repo = gl.search('projects', args.repo)
    if len(repo) == 0:
        sys.exit(f'Could not find {args.repo} on {gl.url}.')
    elif len(repo) > 1:
        repos = '\n'.join([r['path_with_namespace'] for r in repo])
        sys.exit(
            f'More than one repository found that matches the given name:\n'
            f'{repos}\nPlease use a more specific repository name.'
        )
    else:
        repo = gl.projects.get(repo[0]['id'])

    projects = [ ]

    for issue in repo.issues.list(all=True):
        print(f'{issue.iid:03d} {issue.title[:75]:<75}', flush=True)
        p = Project()
        p.iid = issue.iid
        p.title = issue.title
        p.state = issue.state
        p.time_created = dateutil.parser.parse(issue.created_at)
        p.time_updated = dateutil.parser.parse(issue.updated_at)
        p.time_due     = dateutil.parser.parse(issue.due_date) if issue.due_date else None
        p.timeestimate = timedelta(seconds=issue.time_stats()['time_estimate'])
        p.timeestimate_s = issue.time_stats()['time_estimate']
        p.timespent = timedelta(seconds=issue.time_stats()['total_time_spent'])
        p.timespent_s = seconds=issue.time_stats()['total_time_spent']
        p.assignee = ",".join(x['username'] for x in issue.assignees)

        # Get some data from the labels
        for label in issue.labels:
            #print(label)
            if '::' in label:
                namespace, value = label.split('::')
                if namespace == "Unit":
                    p.unit_list.append(value)
                    continue
                elif namespace == "Size":
                    p.size_list.append(value)
                    continue
                elif namespace == "Funding":
                    p.funding_list.append(value)
                    continue
                elif namespace == "Status":
                    p.status_list.append(value)
                    continue
            elif ':' in label:
                key, value = label.split(':')
                if key == 'Task':
                    p.task_list.append(value)
                    continue
                if key == 'Imp':
                    p.importance_list.append(value)
                    continue
            p.label_list.append(label)

        parse_body(p, issue.description)

        note_creation_times = [ p.time_created.year ]
        for note in sorted(issue.notes.list(all=True), key=lambda x: x.created_at):
            created_at = dateutil.parser.parse(note.created_at)
            # The "removed time spent" removes ALL past time spent on the
            # issue, but those notes stay there including the time spent.  So
            # we have to go edit all of the past issues and mark them as
            # time_spent=0.
            if note.body == 'removed time spent':
                p.time_spent_list = [ ]
            # Check the note for time spent
            time_spent_parts = parse_time_spent(note.body)
            if time_spent_parts is not None:
                time_spent = time_to_seconds(*time_spent_parts[:2])
                if time_spent_parts[2]:
                    created_at = TZ.localize(dateutil.parser.parse(time_spent_parts[2]))

                p.time_spent_list.append(
                    (p.iid, created_at, note.author['name'], timedelta(seconds=time_spent))
                    )

            parse_body(p, note.body, created_at=created_at)
            if note.body and note.body.strip().split()[0] not in {'assigned', 'changed', 'subtracted'} and note.body.strip()[0] != '/':
                if len(note.body)<80: print(repr(note.body))
                note_creation_times.append(created_at.year)
        p.year = statistics.median_low(note_creation_times)

        projects.append(p)


    open(args.output, 'wb').write(pickle.dumps(projects))

    # Thank you and goodbye!
    print(f'\nData was written to: {args.output}')


def load(input):
    return _load(open(input, 'rb').read())

def _load(data):
    projects = pickle.loads(data)
    return projects

import pandas as pd
def dataframes(projects):
    """Convert raw dumped data into all the respective dataframes.

    Returns a dict of many dataframes.
    """
    columns = ['iid', 'title', 'state', 'assignee', 'unit', 'funding', 'size', 'status', 'imp',
               'time_created', 'time_due', 'time_updated', 'year',
               #'timeestimate', 'timespent',
               'timeestimate_s',  'timespent_s',
               ]
    # Create the basic df_projects dataframe
    df_projects = pd.DataFrame(
        [[getattr(p, name) for name in columns]
             for p in projects],
        columns=columns,
        )

    # Update types and structure of dataframe
    df_projects['time_created'] = pd.to_datetime(df_projects['time_created'], utc=True).dt.tz_convert(TZ)
    df_projects['time_updated'] = pd.to_datetime(df_projects['time_updated'], utc=True).dt.tz_convert(TZ)
    df_projects['time_due']     = pd.to_datetime(df_projects['time_due'],     utc=True).dt.tz_convert(TZ)
    #df_projects['timespent'] = pd.to_timedelta(df_projects['timespent'], unit='s')
    #df_projects['timeestimate'] = pd.to_timedelta(df_projects['timeestimate'], unit='s')
    df_projects['unit1'] = df_projects['unit'].str.split(':').str[0]
    # year is median of year of all comment times
    df_projects['year1'] = df_projects['time_created'].dt.year
    df_projects.set_index('iid', inplace=True)
    #print(df_projects.info())

    # Timespent separate accounting
    timespent_list = list(itertools.chain(*(p.time_spent_list for p in projects)))
    df_timespent = pd.DataFrame(
        timespent_list,
        columns=['iid', 'time_spentat', 'spender', 'timespent'],
        )
    df_timespent['time_spentat'] = pd.to_datetime(df_timespent['time_spentat'], utc=True).dt.tz_convert(TZ)
    df_timespent['yearmonth'] = df_timespent['time_spentat'].dt.strftime('%Y-%m')
    df_timespent['timespent_s'] = df_timespent['timespent'].dt.total_seconds()
    df_timespent.drop(columns=['timespent'], inplace=True)
    # Infer duration from last match of:
    # - 'Size:' Label
    # - Timeestimate (if greater than zero)
    # - Time spent (if larger than any previous)
    def map_project_size(size):
        sizemap = {'0-G': 1*3600, '1-S': 2*8*3600, '2-M': 10*8*3600, '3-L': 40*8*3600, 'x-NA': 0, None: 0}
        return sizemap[size]
    df_projects['duration_inferred_s'] = df_projects['size'].apply(map_project_size)
    df_projects['size_d'] = df_projects['size'].apply(map_project_size) / (8*3600)
    df_projects.loc[df_projects['timeestimate_s']>0,                               'duration_inferred_s'] = df_projects['timeestimate_s']
    df_projects.loc[df_projects['timespent_s']>df_projects['duration_inferred_s'], 'duration_inferred_s'] = df_projects['timespent_s']
    df_projects['duration_inferred_d'] = df_projects['duration_inferred_s'] / (8*3600)

    # "Task:" labels
    task_list = list(itertools.chain(
                          *([[p.iid, task] for task in p.task_list]
                            for p in projects)))
    #print(task_list)
    df_tasks = pd.DataFrame(
        task_list,
        columns=['iid', 'task'],
        )

    # KPIs
    kpi_list = list(itertools.chain(
                          *([(p.iid,)+kpi for kpi in p.kpi_list]
                            for p in projects)))
    df_kpis = pd.DataFrame(
        kpi_list,
        columns=['iid', 'kpi_name', 'kpi_value', 'time_kpi'],
        )
    df_kpis['time_kpi'] = pd.to_datetime(df_kpis['time_kpi'], utc=True).dt.tz_convert(TZ)

    # Metadata (contact, supervisor, summary) - multi-valued
    metadata_list = list(itertools.chain(
                          *([(p.iid,)+kpi for kpi in p.metadata_list]
                            for p in projects)))
    df_metadata = pd.DataFrame(
        metadata_list,
        columns=['iid', 'metadata_name', 'metadata_value', 'time_metadata'],
        )
    df_metadata['time_metadata'] = pd.to_datetime(df_metadata['time_metadata'], utc=True).dt.tz_convert(TZ)

    # Other labels
    label_list = list(itertools.chain(
                      *([(p.iid, label) for label in p.label_list]
                        for p in projects)))
    df_labels = pd.DataFrame(
        label_list,
        columns=['iid', 'label_name'],
        )


    df_projects = combine_dataframes(
        df_projects,
        df_metadata=df_metadata,
        df_labels=df_labels,
        df_kpis=df_kpis,
        df_tasks=df_tasks)

    return {'df_projects': df_projects,
            'df_timespent': df_timespent,
            'df_tasks': df_tasks,
            'df_kpis': df_kpis,
            'df_metadata': df_metadata,
            'df_labels': df_labels,
            }


def combine_dataframes(df_projects, df_metadata=None, df_labels=None, df_kpis=None, df_tasks=None):
    """Combine many dataframes into a wide dataframe (format subject to change)
    """
    if df_metadata is not None:
        _ = df_metadata.pivot_table(index='iid', aggfunc=','.join, columns='metadata_name', values='metadata_value')
        df_projects = df_projects.join(_, how='left', on='iid')

    if df_labels is not None:
        df_labels = df_labels.copy()
        df_labels['true'] = True
        _ = df_labels.pivot(index='iid', columns='label_name', values='true')
        df_projects = df_projects.join(_, how='left', on='iid')

    if df_kpis is not None:
        _ = df_kpis.pivot_table(index='iid', columns='kpi_name', values='kpi_value', aggfunc='sum')
        _['timesaved_s'] = _.timesaved
        #_['timesaved'] = pd.to_timedelta(_.timesaved, unit='s')
        df_projects = df_projects.join(_, how='left', on='iid')
        df_projects['timesaved_multiplier'] = df_projects['timesaved_s'] / df_projects['timespent_s']

    if df_tasks is not None:
        # one-by-one
        _ = df_tasks.copy()
        _['true'] = True
        _ = _.pivot(index='iid', columns='task', values='true')
        df_projects = df_projects.join(_, how='left', on='iid')
        # all combined
        _ = df_tasks.pivot_table(index='iid', values='task', aggfunc=','.join)
        df_projects = df_projects.join(_, how='left', on='iid')

    return df_projects
