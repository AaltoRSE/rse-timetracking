import sys

import pandas as pd
import plotly.express as px


def report(args):
    data = pd.read_csv(args.input, index_col=0)

    # Parse the timestamps, which includes timezone information. To make sure
    # all times are in the same timezone, we first convert everything to UTC
    # and then to Finnish time (EET).
    data.index = pd.to_datetime(data.index, utc=True).tz_convert('EET')

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

    # Compute time spent per unit, per-month
    time_per_unit_per_month = data.groupby(['unit', pd.Grouper(freq='M', label='left')])[['time_spent']].agg('sum')
    time_per_unit_per_month = time_per_unit_per_month.sort_index()
    time_per_unit_per_month = time_per_unit_per_month.reset_index()
    time_per_unit_per_month['time_spent'] /= (60 * 60 * 8)  # 8-hour work days

    fig_time_per_unit_per_month = px.bar(
        time_per_unit_per_month,
        x='time',
        y='time_spent',
        color='unit',
        barmode='group',
        title='Time spent per unit per month',
        labels=dict(time_spent='time spent (days)', time='month'),
    ).to_html(include_plotlyjs=False, full_html=False, default_width=1000,
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

    # Compute time spent vs. time saved 
    # First, only select project that have a value for time saved
    projects_with_time_saved = data.groupby('iid').agg('sum').query('`timesaved` > 0').index
    time_spent_vs_saved = data[data.iid.isin(projects_with_time_saved)]

    # Compute the total time spent and saved for each group.
    # Use the last date mentioned in the project as representative date.
    time_spent_vs_saved = time_spent_vs_saved.reset_index()[['iid', 'time', 'time_spent', 'timesaved']]
    time_spent_vs_saved.columns = ['iid', 'time', 'time spent', 'time saved']
    time_spent_vs_saved_groups = time_spent_vs_saved.groupby('iid')
    time_spent_vs_saved = time_spent_vs_saved_groups.agg({
        'time': 'max',
        'time spent': 'sum',
        'time saved': 'sum',
    })
    time_spent_vs_saved = time_spent_vs_saved.sort_values('time')

    # Compute cumulative sum over time and convert time into hours
    time_spent_vs_saved['time spent'] = time_spent_vs_saved['time spent'].cumsum() / (60 * 60)
    time_spent_vs_saved['time saved'] = time_spent_vs_saved['time saved'].cumsum() / (60 * 60)

    fig_time_spent_vs_saved = px.line(
        time_spent_vs_saved.melt('time').sort_values('time'),
        x='time',
        y='value',
        color='variable',
        line_group='variable',
        title="Time spent vs. time saved (for projects that track this information)",
        labels=dict(time='date', value='time spent and saved (hours)'),
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
      {time_per_unit_per_month}
      {rse_time}
      {time_spent_vs_saved}
    </body>
    '''

    with open(args.output, 'w') as f:
        f.write(template.format(
            time_per_unit=fig_time_per_unit,
            time_per_unit_per_month=fig_time_per_unit_per_month,
            rse_time=fig_rse_time,
            time_spent_vs_saved=fig_time_spent_vs_saved,
        ))
