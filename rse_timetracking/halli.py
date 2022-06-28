import sys
import dateutil
import pytz
import gitlab

from .time import time_to_seconds, parse_time_spent

TZ = pytz.timezone('Europe/Helsinki')


def halli(args):
    """Main function that serves as the entrypoint to rse_timetracking."""

    year = int(args.year)
    month = int(args.month)

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

    # Store time spent in dicts for each day
    days = [{} for day in range(0, 31)]

    # Now check all issues. Find funding type and time spent on each day.
    for issue in repo.issues.list(all=True):

        # Check funding type
        funding = "unknown"
        for label in issue.labels:
            try:
                namespace, content = label.split('::')
                if namespace == "Funding":
                    funding = content
                    if funding not in days[0]:
                        for day in range(0, 31):
                            days[day][funding] = 0
            except ValueError:
                # Label doesn't follow namespace::content pattern
                pass

        # Check **all** notes and find time spent given month
        for note in sorted(issue.notes.list(all=True), key=lambda x: x.created_at):
            if note.author['name'] == args.name:
                created_at = dateutil.parser.parse(note.created_at)
                # Check the note for time spent
                time_spent_parts = parse_time_spent(note.body)
                if time_spent_parts is not None:
                    if time_spent_parts[2]:
                        created_at = TZ.localize(dateutil.parser.parse(time_spent_parts[2]))
                    if created_at.year == year and created_at.month == month:
                        time_spent = time_to_seconds(*time_spent_parts[:2])/3600
                        days[created_at.day-1][funding] += time_spent

    # For formatting: find funding types with non-zero time spent
    nonzero_types = []
    for index, records in enumerate(days):
        for type, time in records.items():
            if type not in nonzero_types and time > 0:
                nonzero_types.append(type)

    # Now print records for each day
    for index, records in enumerate(days):
        date = index+1
        unallocated_time = 7.25
        print(f"{date}: ", end="")
        for type in nonzero_types:
            time = records[type]
            if type not in ["unknown", 'Unit']:
                unallocated_time -= time
                print(f"{type}={time} ", end="")
        print(f"Base={unallocated_time}")


if __name__ == '__main__':
    import argparse, sys

    parser=argparse.ArgumentParser()

    parser.add_argument('-m', '--month', help='The month as an integer')
    parser.add_argument('-y', '--year', help='The year as an integer')
    parser.add_argument('-n', '--name', help='Your name')
    parser.add_argument('-i', '--input', help='Input file name',
                        default='report.csv')
    parser.add_argument('--repo', default='rse-projects',
                          help=('The name of the repository that tracks the '
                                'projects. Defaults to AaltoRSE/rse-projects'))

    args=parser.parse_args()

    halli(args)
