"""
Scrape version.aalto.fi to assemble statistics about RSE projects. For each
project, Key Performance Indicators (KPIs) are gathered from the issue tracker.
"""
import sys
from collections import defaultdict
import dateutil

import gitlab
import pandas as pd

from .time import time_to_seconds, parse_time_spent
from .kpis import parse_KPIs


def scrape(args):
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

    issue_records = []

    print(f'    Issue title                                                 Total time spent', flush=True)  # noqa
    print(f'--------------------------------------------------------------------------------', flush=True)  # noqa

    for issue in repo.issues.list(all=True):
        # track time spent here
        time_spent = defaultdict(int)

        # Each KPI is counted per person, so there are two layers of dicts
        KPIs = defaultdict(lambda: defaultdict(int))

        # Track whether the issue was closed
        is_closed = False

        for note in issue.notes.list(all=True):
            # Parse the note
            author = note.author['name']

            # Check the note for time spent
            time_spent_parts = parse_time_spent(note.body)
            if time_spent_parts is not None:
                t = time_to_seconds(*time_spent_parts)
                time_spent[author] += t

            if note.body == "closed":
                is_closed = True
            # TODO: switching status to re-opened

            # Issue number, time spent, time saved, etc.
            issue_record = dict(
                time=note_creation_dates.append(dateutil.parser.parse(note.created_at)),
                author=author,
                time_spent=t,
                iid=issue.iid,
                project=issue.title,
                unit=unit,
                funding=funding,
                is_closed=is_closed,
            )

            # Check KPIs
            KPI_parts = parse_KPIs(note.body)
            if KPI_parts is not None:
                KPI_name, KPI_value = KPI_parts
                issue_record[KPI_name] += KPI_value

        ## Determine dates during which the issue/project was active
        #if len(note_creation_dates) == 0:
        #    date_start = None
        #    date_end = None
        #else:
        #    date_start = min(note_creation_dates)
        #    date_end = max(note_creation_dates)

        # Done with notes
        # Now check the labels
        funding = 'Unknown'
        for label in issue.labels:
            namespace, content = label.split('::')
            if namespace == "Unit":
                unit = content
            elif namespace == "Funding":
                funding = content


        for KPI_name, KPI_values in KPIs.items():
            for author, KPI_value in KPI_values.items():
                issue_record[f'{KPI_name} by {author}'] = KPI_value

        for author, time in time_spent.items():
            issue_record[f'Time spent by {author}'] = time
        total_time_spent = sum(time_spent.values())
        issue_record['Total time spent'] = total_time_spent

        issue_records.append(issue_record)
        print(f'{issue.iid:03d} {issue.title[:68]:<68} {total_time_spent:>7d}',
              flush=True)

    data = pd.DataFrame(issue_records)
    data.to_csv(args.output, index=False)

    # Thank you and goodbye!
    print(f'\nData was written to: {args.output}')
