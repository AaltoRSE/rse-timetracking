"""
Scrape version.aalto.fi to assemble statistics about RSE projects. For each
project, Key Performance Indicators (KPIs) are gathered from the issue tracker.
"""
from argparse import ArgumentParser
import sys
from collections import defaultdict

import gitlab
import pandas as pd

from .time import time_to_seconds, parse_time_spent
from .kpis import KPI_defs, parse_KPIs


def scrape():
    # Parse command line arguments
    p = ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, help='The year to scrape.')
    p.add_argument('-o', '--output', nargs='?', type=str, default=None,
                   help=('The .csv file to write the scraped data to. '
                         'Defaults to report_<year>.csv'))
    p.add_argument('--repo', type=str, default='AaltoRSE/rse-projects',
                   help=('The name of the repository that tracks the '
                         'projects. Defaults to AaltoRSE/rse-projects'))
    args = p.parse_args()

    # This default value needs to be computed from other arguments
    if args.output is None:
        args.output = f'report_{args.year}.csv'

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

    # Create an empty python dataframe and define the columns.
    # This will contain the issue numer and name, the amount of RSE time spent,
    # all the KPIs defined above and unit and funding information.
    data = pd.DataFrame([], columns=["#", "Project", "RSE time spent"] +
                                    [KPI['name'] for KPI in KPI_defs] +
                                    ["Unit", "Funding", "Closed"])

    # Check all issues in case they were active in the desired year
    for issue in repo.issues.list(all=True):
        # Note if this project was active in 2020. If any note is active,
        # this will be switched to True
        active = False

        # Create a list of KPIs. Each will also be counted per person,
        # so there are two layers of dicts
        KPIs = defaultdict(lambda: defaultdict(int))

        # track time spent here
        time_spent = defaultdict(int)

        # Track whether the issue was closed
        is_closed = False

        for note in issue.notes.list(all=True):
            # Parse only notes created in the specified year
            if note.created_at.startswith(str(args.year)):
                # Check the note for time spent
                t_string, added_or_subtracted = parse_time_spent(note.body)
                t = time_to_seconds(t_string, added_or_subtracted)
                if t is not None:
                    time_spent[note.author['name']] += t

                # if time spent is nozero, the issue is active
                if t:
                    active = True

                # Check KPIs
                KPI, value = parse_KPIs(note.body)
                if KPI is not None:
                    KPIs[KPI][note.author['name']] += value

                    # Found a note during the given year, so the project was
                    # active
                    if t:
                        active = True

                if note.body == "closed":
                    is_closed = True

        # Tally up everything
        total_time_spent = sum(time_spent.values())
        KPI_sums = []
        for KPI in KPI_defs:
            KPI_sums.append(sum(KPIs[KPI['name']].values()))

        # Done with notes
        # Now check the labels
        funding = 'Unknown'
        for label in issue.labels:
            namespace, content = label.split('::')
            if namespace == "Unit":
                unit = content
            if namespace == "Funding":
                funding = content

        # Issue number, time spent, time saved
        if active:
            data.loc[len(data)] = ([issue.iid, issue.title, total_time_spent] +
                                   KPI_sums + [unit, funding, is_closed])

    # create a csv_file
    data.to_csv(args.output, index=False)

    # Display the dataframe as a table
    print(data)

    # Thank you and goodbye!
    print(f'Data was written to: {args.output}')


if __name__ == '__main__':
    scrape()