from argparse import ArgumentParser
import sys

from .scrape import scrape
from .scrape2 import scrape2
from .report import report
from .halli import halli


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
    p_scrape.add_argument('--v2', action='store_true',
                          help=('Use new version'))

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

    # Halli sub-command
    p_halli = sub_parsers.add_parser('halli', help='Report hours spent for Halli')
    p_halli.add_argument('-m', '--month', help='The month as an integer')
    p_halli.add_argument('-y', '--year', help='The year as an integer')
    p_halli.add_argument('-n', '--name', help='Your name')
    p_halli.add_argument('-i', '--input', help='Input file name',
                        default='report.csv')
    p_halli.add_argument('--repo', default='rse-projects',
                          help=('The name of the repository that tracks the '
                                'projects. Defaults to AaltoRSE/rse-projects'))


    args = parser.parse_args()

    if args.command == 'scrape':
        if args.v2:
            scrape2(args)
        else:
            scrape(args)
    elif args.command == 'report':
        report(args)
    elif args.command == 'halli':
        halli(args)
    else:
        parser.print_help()
        sys.exit(1)
