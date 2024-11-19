import plotly.graph_objects as go
from plotly.subplots import make_subplots
import params
from uncoordinated_scenario_1 import df as df1
from uncoordinated_scenario_1 import avg_daily_peak as avg_daily_peak1
from coordinated_scenario_1 import (model, df, avg_daily_peak)


# graph colours
household_load_colour = 'red'
ev_load_colour = 'black'
total_load_colour = '#00cc96'
avg_daily_peak_colour = 'blue'


fig = make_subplots(rows=2, cols=1,
                    subplot_titles=('Uncoordinated Scenario', 'Coordinated Scenario'))

# uncoordinated scenario
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['household_load'],
                         name='Household Load',
                         legendgroup='1',
                         mode='lines',
                         marker={'color': household_load_colour}), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['ev_load'],
                         name='EV Load',
                         legendgroup='1',
                         mode='lines',
                         marker={'color': ev_load_colour}), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['total_load'],
                         name='Total Load',
                         legendgroup='1',
                         mode='lines',
                         marker={'color': total_load_colour}), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=[avg_daily_peak1 for i in range(len(df1.index))],
                         name='Average daily peak',
                         legendgroup='1',
                         mode='lines',
                         marker={'color': avg_daily_peak_colour}), row=1, col=1)


# coordinated scenario
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.household_load,
                         name='Household Load',
                         legendgroup='2',
                         mode='lines',
                         marker={'color': household_load_colour}), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.ev_load,
                         name='EV Load',
                         legendgroup='2',
                         mode='lines',
                         marker={'color': ev_load_colour}), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.total_load,
                         name='Total Load',
                         legendgroup='2',
                         mode='lines',
                         marker={'color': total_load_colour}), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=[avg_daily_peak for i in range(len(model.TIME))],
                         name='Average daily peak',
                         legendgroup='2',
                         mode='lines',
                         marker={'color': avg_daily_peak_colour}), row=2, col=1)


fig.update_layout(xaxis2_title='Timestamp',
                  yaxis1_title='Load (kW)',
                  yaxis2_title='Load (kW)',
                  height=600, width=1000,
                  legend_tracegroupgap=180,
                  title_text=f'Load Profile ({params.num_of_households} Households and {params.num_of_evs} EVs) - '
                             f'Comparison of Scenarios - {params.tariff_type.title()} Tariff')
fig.show()
