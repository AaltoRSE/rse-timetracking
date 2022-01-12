"""
Scrape version.aalto.fi to assemble statistics about RSE projects. For each
project, Key Performance Indicators (KPIs) are gathered from the issue tracker.
"""
import sys
from collections import defaultdict
import dateutil
import pytz

import gitlab
import pandas as pd

from .time import time_to_seconds, parse_time_spent
from .kpis import parse_KPIs

TZ = pytz.timezone('Europe/Helsinki')


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

    for issue in repo.issues.list(all=True):
        # Get some data from the labels
        unit = []
        funding = []
        status = []
        for label in issue.labels:
            try:
                namespace, content = label.split('::')
                if namespace == "Unit":
                    unit.append(content)
                elif namespace == "Funding":
                    funding.append(content)
                elif namespace == "Status":
                    status.append(content)
            except ValueError:
                # Label doesn't follow namespace::content pattern
                pass
        # There should be only one of these, but this isn't enforced.
        # But in case there is more than one, pass all through so that
        # errors don't pass silently.
        unit = '-'.join(unit)
        funding = '-'.join(funding)
        status = '-'.join(status)
        if funding == '':
            funding = 'Unknown'

        #import IPython ; IPython.embed()
        issue_record = dict(
            iid=issue.iid,
            project=issue.title,
            unit=unit,
            funding=funding,
            state=issue.state,
            status=status,
            # above common for all rows, bottom specific
            time_created=dateutil.parser.parse(issue.created_at),
            time=dateutil.parser.parse(issue.created_at),
            assignee=",".join(x['username'] for x in issue.assignees),
            time_estimate=issue.time_stats()['time_estimate'],
            total_time_spent=issue.time_stats()['total_time_spent'],
        )
        issue_records.append(issue_record)


        print(f'{issue.iid:03d} {issue.title[:75]:<75}', flush=True)
        for note in sorted(issue.notes.list(all=True), key=lambda x: x.created_at):
            created_at = dateutil.parser.parse(note.created_at)
            # The "removed time spent" removes ALL past time spent on the
            # issue, but those notes stay there including the time spent.  So
            # we have to go edit all of the past issues and mark them as
            # time_spent=0.
            if note.body == 'removed time spent':
                for old_row in issue_records:
                    if old_row['iid'] == issue.iid:
                        old_row['time_spent'] = 0
            # Check the note for time spent
            time_spent_parts = parse_time_spent(note.body)
            if time_spent_parts is not None:
                time_spent = time_to_seconds(*time_spent_parts[:2])
                if time_spent_parts[2]:
                    created_at = TZ.localize(dateutil.parser.parse(time_spent_parts[2]))
            else:
                time_spent = 0
                #print(note.body)

            # Issue number, time spent, time saved, etc.
            issue_record = dict(
                iid=issue.iid,
                project=issue.title,
                unit=unit,
                funding=funding,
                state=issue.state,
                status=status,
                # above common for all rows, bottom specific
                time=created_at,
                author=note.author['name'],
                time_spent=time_spent,
                is_closed=note.body == 'closed',
                # TODO: switching status to re-opened
            )

            # Check KPIs
            for KPI_parts in parse_KPIs(note.body):
                KPI_name, KPI_value = KPI_parts
                issue_record[KPI_name] = KPI_value

            issue_records.append(issue_record)


    data = pd.DataFrame(issue_records)
    data.to_csv(args.output, index=False)

    # Thank you and goodbye!
    print(f'\nData was written to: {args.output}')
