import plotly.graph_objects as go
from plotly.subplots import make_subplots
import params
from models.uncoordinated_scenario_1 import df as df1
from models.uncoordinated_scenario_1 import avg_daily_peak as avg_daily_peak1
from models.coordinated_scenario_1 import (model, df, avg_daily_peak)


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





# ------------------- results visualisation ------------------- #

def visualise_results(model, df, avg_daily_peak, num_of_evs):
    # flat tariff plot
    flat_tariff_fig = go.Figure()
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.household_load, name='Household Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.ev_load, name='EV Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.total_load, name='Total Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                         y=[avg_daily_peak for i in range(len(model.TIME))],
                                         name='Average daily peak'))

    flat_tariff_fig.update_layout(
        title=f'Load Profile ({params.num_of_households} Households and {num_of_evs} EVs) - '
              f'Coordinated Scenario - {params.tariff_type.title()} Tariff',
        xaxis_title='Timestamp',
        yaxis_title='Load (kW)')

    # ToU tariff plot
    # Create figure with secondary y-axis
    # tou_tariff_fig = make_subplots(specs=[[{"secondary_y": True}]])
    tou_tariff_fig = make_subplots(rows=2, cols=1,
                                   subplot_titles=(
                                       f'Load Profile ({params.num_of_households} Households and {num_of_evs} EVs) - '
                                       f'Coordinated Scenario - {params.tariff_type.title()} Tariff', 'Price Signal'))

    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.household_load,
                                        name='Household Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.ev_load,
                                        name='EV Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.total_load,
                                        name='Total Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=[avg_daily_peak for i in range(len(model.TIME))],
                                        name='Average daily peak'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=[i for i in params.tou_tariff['tariff']],
                                        name='ToU tariff'),
                             # secondary_y=True,
                             row=2, col=1)

    tou_tariff_fig.update_layout(xaxis2_title='Timestamp',
                                 yaxis1_title='Load (kW)',
                                 yaxis2_title='Price ($/kW)')

    # tou_tariff_fig.update_layout(
    #     title=f'Load Profile ({params.num_of_households} Households and {num_of_evs} EVs) - '
    #           f'Coordinated Scenario - {params.tariff_type.title()} Tariff')

    # Set x-axis title
    # tou_tariff_fig.update_xaxes(title_text='Timestamp')

    # Set y-axes titles
    # tou_tariff_fig.update_yaxes(title_text='Tariff ($/kW)', secondary_y=True)
    # tou_tariff_fig.update_yaxes(title_text='Load (kW)', secondary_y=False)

    def plot_results():
        if params.tariff_type == 'flat':
            flat_tariff_fig.show()
        elif params.tariff_type == 'tou':
            tou_tariff_fig.show()

    plot_results()


# visualise_results(df, avg_daily_peak)

def plot_each_ev(model, ev_id):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=params.timestamps, y=[pyo.value(model.SOC_EV[ev_id, t]) for t in model.TIME],
                             name='SOC'))
    fig.add_trace(go.Scatter(x=params.timestamps, y=[pyo.value(model.P_EV[ev_id, t]) for t in model.TIME],
                             name='Charging Power'))

    fig.update_layout(title=f'SOC and Charging Power of EV_ID{ev_id} - Coordinated Scenario',
                      xaxis_title='Timestamp')
    fig.show()

# for i in range(num_of_evs):
#     plot_each_ev(i)




# ------------------- results visualisation ------------------- # uncoordinated scenario

peak_total = []
for day in set(df.index.day):
    daily_peak = df.loc[(df.index.day == day), 'household_load'].max()
    peak_total.append(daily_peak)

avg_daily_peak = sum(peak_total) / len(peak_total)
print(avg_daily_peak)

fig = go.Figure()

fig.add_trace(go.Scatter(x=df.index, y=df['household_load'], name='Household Load'))
fig.add_trace(go.Scatter(x=df.index, y=df['ev_load'], name='EV Load'))
fig.add_trace(go.Scatter(x=df.index, y=df['total_load'], name='Total Load'))
fig.add_trace(
    go.Scatter(x=df.index, y=[avg_daily_peak for i in range(len(df.index))], name='Average daily peak'))
fig.update_layout(title=f'Load Profile ({params.num_of_households} Households and {params.num_of_evs} EVs) - Uncoordinated Scenario',
                  xaxis_title='Timestamp',
                  yaxis_title='Load (kW)')
fig.show()
