from argparse import ArgumentParser
import sys

from .scrape import scrape
from .report import report


def main():
    # Parse command line arguments
    parser = ArgumentParser(description=__doc__)
    sub_parsers = parser.add_subparsers(dest='command')

    # Scrape sub-command
    p_scrape = sub_parsers.add_parser('scrape', help='Scrape Gitlab')
    p_scrape.add_argument('-o', '--output', default='report.csv',
                          help=('The .csv file to write the scraped data to. '
                                'Defaults to report.csv'))
    p_scrape.add_argument('--repo', default='rse-projects',
                          help=('The name of the repository that tracks the '
                                'projects. Defaults to AaltoRSE/rse-projects'))

    # Report sub-command
    p_report = sub_parsers.add_parser('report', help='Build HTML report')
    p_report.add_argument('-i', '--input', default='report.csv',
                          help=('The .csv file to read the statistics from. '
                                'Defaults to report.csv'))
    p_report.add_argument('-o', '--output', default='report.html',
                          help=('The .html file to write the report to. '
                                'Defaults to report.html'))
    p_report.add_argument('-y', '--year', type=int, default=None,
                          help=('Restrict report to a specific year.'
                                'Defaults to reporting on all years'))

    args = parser.parse_args()

    if args.command == 'scrape':
        scrape(args)
    elif args.command == 'report':
        report(args)
    else:
        parser.print_help()
        sys.exit(1)
