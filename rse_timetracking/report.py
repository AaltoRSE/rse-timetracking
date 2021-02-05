import sys

import pandas as pd
from jinja2 import Template
import plotly.express as px


def report(args):
    data = pd.read_csv(args.input, index_col=0)
    RSEs = set([col.split(' by ')[1] for col in data.columns
                if ' by ' in col])
    KPIs = set([col.split(' by ')[0] for col in data.columns
                if ' by ' in col and not col.startswith('Time spent')])

    # Compute total time spent
    time_spent_cols = [f'Time spent by {RSE}' for RSE in RSEs]
    data['Total time spent'] = data[time_spent_cols].sum(axis=1)

    # Compute time spent per unit
    time_per_unit = data.groupby('unit')[['Total time spent']].agg('sum')
    time_per_unit = time_per_unit.sort_index()
    time_per_unit = time_per_unit.reset_index()

    fig_time_per_unit = px.pie(
        time_per_unit,
        values='Total time spent',
        names='unit',
        title='Time spent per unit',
    ).to_html(include_plotlyjs=False, full_html=False, default_width=400,
              default_height=400)

    # Compute how each RSE spent their time. The percentage of time dedicated
    # to each unit.
    rse_time = data[['unit'] + time_spent_cols].groupby('unit').agg('sum')
    rse_time /= rse_time.sum()
    rse_time *= 100
    rse_time = rse_time.stack().reset_index()
    rse_time.columns = ['Unit', 'RSE', 'Time spent (%)']
    rse_time['RSE'] = rse_time['RSE'].str.lstrip('Time spent by ')
    rse_time = rse_time.sort_values('Unit')

    fig_rse_time = px.bar(
        rse_time,
        x="RSE",
        y="Time spent (%)",
        color="Unit",
        title="Time spent by each RSE"
    ).to_html(include_plotlyjs=False, full_html=False, default_width=600,
              default_height=400)

    with open('templates/main.html') as f:
        template = Template(f.read())

    with open(args.output, 'w') as f:
        f.write(template.render(
            time_per_unit=fig_time_per_unit,
            rse_time=fig_rse_time,
        ))
