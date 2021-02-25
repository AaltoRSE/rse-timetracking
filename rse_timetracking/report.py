import sys

import pandas as pd
import plotly.express as px


def report(args):
    data = pd.read_csv(args.input, index_col=0)

    # Filter data by date
    if args.year is not None:
        date_mask = data['date_start'].map(lambda date: date.year) <= args.year
        date_mask &= data['date_end'].map(lambda date: date.year) >= args.year
        data = data[date_mask]

    RSEs = set([col.split(' by ')[1] for col in data.columns
                if ' by ' in col])
    KPIs = set([col.split(' by ')[0] for col in data.columns
                if ' by ' in col and not col.startswith('Time spent')])

    # Compute time spent per unit
    time_per_unit = data.groupby('unit')[['time_spent']].agg('sum')
    time_per_unit = time_per_unit.sort_index()
    time_per_unit = time_per_unit.reset_index()

    fig_time_per_unit = px.pie(
        time_per_unit,
        values='time_spent',
        names='unit',
        title='Time spent per unit',
    ).to_html(include_plotlyjs=False, full_html=False, default_width=400,
              default_height=400)

    # Compute how each RSE spent their time. The percentage of time dedicated
    # to each unit.
    rse_time = data.groupby(['author', 'unit']).agg('sum')['time_spent']
    rse_time /= rse_time.groupby('author').transform('sum')
    rse_time *= 100
    rse_time = rse_time.reset_index()
    rse_time.columns = ['RSE', 'Unit', 'Time spent (%)']
    rse_time = rse_time.sort_values(['RSE', 'Unit'])

    fig_rse_time = px.bar(
        rse_time,
        x="RSE",
        y="Time spent (%)",
        color="Unit",
        title="Time spent by each RSE"
    ).to_html(include_plotlyjs=False, full_html=False, default_width=600,
              default_height=400)

    template = r'''
    <html>
    <head>
      <meta charset="utf-8" />
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script> 
    </head>
    <body>
      <h1>RSE statistics</h1>
      {time_per_unit}
      {rse_time}
    </body>
    '''

    with open(args.output, 'w') as f:
        f.write(template.format(
            time_per_unit=fig_time_per_unit,
            rse_time=fig_rse_time,
        ))
