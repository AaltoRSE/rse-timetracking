import sys

import pandas as pd


def report(args):
    report = pd.read_csv(args.input, index_col=0)
    print(report.sum().sort_index()[:-4])
    print()
    print(report.groupby('unit').agg('sum'))
