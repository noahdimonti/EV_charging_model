import plotly.graph_objects as go
from plotly.subplots import make_subplots
import params
from uncoordinated_scenario_1 import df as df1
from uncoordinated_scenario_1 import avg_daily_peak as avg_daily_peak1
from coordinated_scenario_1 import (model, df, avg_daily_peak)

fig = make_subplots(rows=2, cols=1,
                    subplot_titles=('Uncoordinated Scenario', 'Coordinated Scenario'))

# uncoordinated scenario
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['household_load'],
                         name='Household Load',
                         legendgroup='1'), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['ev_load'],
                         name='EV Load',
                         legendgroup='1'), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=df1['total_load'],
                         name='Total Load',
                         legendgroup='1'), row=1, col=1)
fig.add_trace(go.Scatter(x=df1.index,
                         y=[avg_daily_peak1 for i in range(len(df1.index))],
                         name='Average daily peak',
                         legendgroup='1'), row=1, col=1)
# fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Uncoordinated Scenario',
#                   xaxis_title='Timestamp',
#                   yaxis_title='Load (kW)')

# coordinated scenario
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.household_load,
                         name='Household Load',
                         legendgroup='2'), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.ev_load,
                         name='EV Load',
                         legendgroup='2'), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.total_load,
                         name='Total Load',
                         legendgroup='2'), row=2, col=1)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=[avg_daily_peak for i in range(len(model.TIME))],
                         name='Average daily peak',
                         legendgroup='2'), row=2, col=1)

# fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Comparison of Uncoordinated and Coordinated Scenarios',
#                   xaxis_title='Timestamp',
#                   yaxis_title='Load (kW)')

fig.update_layout(xaxis2_title='Timestamp',
                  yaxis1_title='Load (kW)',
                  yaxis2_title='Load (kW)',
                  height=600, width=1000,
                  legend_tracegroupgap=180,
                  title_text=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Comparison of Uncoordinated and Coordinated Scenarios')
fig.show()
