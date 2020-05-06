
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd 
import json
import numpy as np
from datetime import datetime, timedelta


def gen_state_trend_plot(days_since_start_of_2020,scaling,current_vs_cumulative,field):
    df = state_df
    if scaling == 'linear':
        column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        axis_type = 'linear'
        ymin = 0
        ymax = df[column_string].max()*1.1
    else:
        column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        axis_type = 'log'
        ymin = np.log10(df[column_string].min())
        ymax = np.log10(df[column_string].max()*1.1)
    if field == 'deaths': field_string = 'Deaths'
    else: field_string = 'Cases'
    if current_vs_cumulative == 'cumulative': 
        #title_string = f'Cumulative {field_string} per 100,000 people'
        ylabel = f'Cumulative Covid {field_string} per 100,000'
    else:
        #title_string = f'Average Daily {field_string} per 100,000 people over last week'
        ylabel = f'Average Daily Covid {field_string} per 100,000'
    data = []
    for state in df['state'].unique():
        dfs = df[df['state']==state]
        data.append(go.Scatter(x=dfs['datetime'], y=dfs[column_string], line=dict(color='black', width=0.1), opacity=0.8, showlegend=False, name=state))
    layout = go.Layout(
            hovermode='closest', 
            xaxis={"title":"Date", "range":["2020-03-01","2020-05-05"]}, 
            yaxis={"title":ylabel, "type":axis_type, "range":[ymin,ymax]}
        )
    return {"data" : data, "layout" : layout}

def update_state_trend_plot(hover_data,original_figure,current_figure,days_since_start_of_2020,scaling,current_vs_cumulative,field):
    try:
        GUI_state = hover_data['points'][0]['location']
    except:
        return original_figure
    data = original_figure['data']
    df = state_df
    dfs = df[df['state']==GUI_state]
    if scaling == 'linear':
        column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        ymin = 0
        ymax = df[column_string].max()*1.1
    else:
        column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        ymin = np.log10(df[column_string].min())
        ymax = np.log10(df[column_string].max()*1.1)
    data.append(go.Scatter(x=dfs['datetime'], y=dfs[column_string], line=dict(color='black', width=1), opacity=1, name=GUI_state))
    selected_date = (pd.datetime(2020,1,1)+timedelta(days=days_since_start_of_2020)).strftime('%Y-%m-%d')
    data.append(go.Scatter(x=[selected_date,selected_date], y=[ymin,ymax], line=dict(color='blue', width=2), opacity=0.2, name=selected_date, mode='lines'))
    return {"data" : data, "layout" : original_figure['layout']}

def gen_map(date,geography,scaling,current_vs_cumulative,field):
    datestring = (start_of_2020+timedelta(days=date)).strftime('%Y-%m-%d')
    if geography == 'states': 
        df = state_df[state_df['datetime']==datestring]
        locationmode = 'USA-states'
        projection = 'albers usa'
        if scaling == 'linear':
            column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        else:
            column_string = 'log_'+current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        max_value = state_df[column_string].max()
        min_value = state_df[column_string].min()
    elif geography == 'counties': df = county_df
    elif geography == 'world': df = ''
    else:
        raise ValueError('Unrecognized geography %s' % (geography))
    # figure = px.choropleth(
    #         data_frame = df,
    #         locations = 'state',
    #         color = current_vs_cumulative+'_'+field+'_per_hundred_thousand',
    #         locationmode = locationmode,
    #         scope="usa")
    # cmin = np.min(df[column_string])
    # cmax = np.max(df[column_string])
    # cvals = np.linspace(cmin,cmax,8)
    # if scaling == 'log':
    #     ctext = (10**cvals).round(2)
    #     cvals = np.log10(ctext)
    # else:
    #     ctext = cvals.round(2)
    #     cvals = ctext
    if scaling == 'log':
        tickprefix = '10^'
    else:
        tickprefix = ''
    data = [go.Choropleth(
            locations = df['state'],
            z = df[column_string],
            locationmode = 'USA-states',
            colorscale = 'RdBu',
            #autocolorscale=False,
            #colorbar_title=current_vs_cumulative+' '+field+' per_hundred_thousand'
            reversescale = True, 
            #zmid = 0,
            zmin = min_value,
            zmax = max_value,
            text = df[column_string.replace("log_","")],
            hoverinfo='location+text',
            #colorbar = go.choropleth.ColorBar(tickmode='array', tickvals=cvals, ticktext=ctext)
            colorbar = go.choropleth.ColorBar(tickprefix=tickprefix)
            #colorbar = go.choropleth.ColorBar(
            #    title = radio, tickvals=[-30,-20,-10,0,10,20,30], 
            #    ticktext=['R+30'+extra_space,'R+20'+extra_space,'R+10'+extra_space,'Even'+extra_space,'D+10'+extra_space,'D+20'+extra_space,'D+30'+extra_space]))]
            )]
    layout = go.Layout(
        #title = go.layout.Title(
        #    text = '2016 Presidential Election'
        #),
        geo = go.layout.Geo(
            showframe = False,
            showcoastlines = False,
            projection = go.layout.geo.Projection(
                type = 'albers usa'
            )
        ),
        height=550
    )
    figure={
        'data': data,
        'layout': layout,
        }    
    return figure    

start_of_2020 = datetime(2020,1,1)
support_counties = False
support_states = True
support_history = True

if support_counties:
    # get shapes of county outlines
    counties = pd.read_json('geojson-counties-fips.json')
    # # read county-level data
    # county_df = read_data('https://raw.githubusercontent.com/nytimes/covid-19-data/master/','us-counties.csv')
    # county_df['datetime'] = pd.to_datetime(county_df['date'])
    # # county_df columns: date, datetime, county, state, fips, cases, deaths
    # county_dates = county_df['datetime'].unique()
    jh_death_data = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/','time_series_covid19_deaths_US.csv')
    jh_case_data = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/','time_series_covid19_confirmed_US.csv')


if support_states:
    state_df = pd.read_csv('us_data.csv')
if support_history:
    history_df = pd.read_csv('us_death_trends.csv')
    typical_df = pd.read_csv('us_typical_deaths.csv')

state_dates = state_df['datetime'].unique()

geography = 'counties'
current_vs_cumulative = 'cumulative'
field = 'deaths'
scaling = 'log'

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    id = "root",
    children = [
        html.Div(
            id="header",
            children=[
                html.H4(children="Covid-19")
            ]
        ),
        html.Div(
            id="slider-container",
            children=[
                html.P(
                    id="slider-text",
                    children="Drag the slider to change the date:",
                ),
                dcc.Slider(
                    id="date-slider",
                    #min=min(state_dates),
                    #max=max(state_dates),
                    #value=max(state_dates),
                    #marks={str(date): str(date) for date in state_dates}
                    min=(pd.to_datetime(min(state_dates))-start_of_2020).days,
                    max=(pd.to_datetime(max(state_dates))-start_of_2020).days,
                    value=(pd.to_datetime(max(state_dates))-start_of_2020).days
                    #step=None
                ),
                dcc.RadioItems(
                    id="radio-current-vs-cumulative",
                    options=[
                        {'label': 'Average over last 7 days', 'value': '7day_avg'},
                        {'label': 'Cumulative', 'value': 'cumulative'}
                    ],
                    value='7day_avg'
                ),
                dcc.RadioItems(
                    id="radio-field",
                    options=[
                        {'label': 'Confirmed Cases', 'value': 'cases'},
                        {'label': 'Deaths', 'value': 'deaths'},
                        #{'label': 'Hospitalizations', 'value': 'hospitalizations'},
                        #{'label': 'In ICU', 'value': 'icu'},
                        #{'label': 'On Ventilator', 'value': 'ventilators'},
                        #{'label': 'Tests', 'value': 'tests'}
                    ],
                    value='deaths'
                ),
                dcc.RadioItems(
                    id="radio-scaling",
                    options=[
                        {'label': 'Logarithmic', 'value': 'log'},
                        {'label': 'Linear', 'value': 'linear'}
                    ],
                    value='linear'
                ),
                dcc.RadioItems(
                    id="radio-geography",
                    options=[
                        {'label': 'US States', 'value': 'states'},
                        #{'label': 'US Counties', 'value': 'counties'},
                        #{'label': 'World', 'value': 'world'}
                    ],
                    value='states'
                )
            ]
        ),
        html.Div(
            id="heatmap-container",
            children=[
                html.P("Choropleth Map for ",
                    id="heatmap-title"
                ),
                dcc.Graph(
                    id='choropleth'
                )
            ]
        ),
        html.Div([
            html.P("Hovering over a state on the map will bring up details on that state in the two figures below.  The lower left figure shows the history of the selected quantity (cases or deaths, cumulatively or daily averages over the last week).  The lower right figure shows the (total) death rates (from all causes) throughout the calendar year for the selected state with 2020 in red and 2017, 2018, and 2019 in gray.  The green line is the average of the 2017-2019 death rates + reported Covid fatalities.  Both figures include a vertical blue line indicating the date of the data being displayed in the map above."),
        ]),
        html.Div([
            dcc.Store(id='state-trends-stash'),
            dcc.Graph(id='state-trends'),
            dcc.Graph(id='state-history')
        ], style={'columnCount': 2})
    ]
)


@app.callback(Output("choropleth", "figure"),
    [
        Input("date-slider", "value"),
        Input("radio-geography", "value"),
        Input("radio-scaling", "value"),
        Input("radio-current-vs-cumulative", "value"),
        Input("radio-field", "value")
    ]
)
def display_map(date,geography,scaling,current_vs_cumulative,field):
    return gen_map(date,geography,scaling,current_vs_cumulative,field)

@app.callback(Output("heatmap-title", "children"), 
    [
        Input("date-slider", "value"), 
        Input("radio-current-vs-cumulative", "value"),
        Input("radio-field", "value")
    ]
)
def update_map_title(days_since_start_of_2020,current_vs_cumulative,field):
    date_string = (start_of_2020+timedelta(days=days_since_start_of_2020)).strftime('%Y-%m-%d')
    if field == 'deaths': field_string = 'Deaths Reported'
    else: field_string = 'Cases Reported'
    if current_vs_cumulative == 'cumulative': 
        title_string = f'Cumulative Covid-19 {field_string} per 100,000 people'
    else:
        title_string = f'Average Daily Covid-19 {field_string} per 100,000 people over last week'
    return f"{title_string} as of {date_string}"

@app.callback(Output("radio-field", "options"), [Input("radio-geography", "value")])
def update_field_options(geography):
    if geography == 'states':
        options=[
            {'label': 'Confirmed Cases', 'value': 'cases'},
            {'label': 'Deaths', 'value': 'deaths'},
            #{'label': 'Hospitalizations', 'value': 'hospitalizations'},
            #{'label': 'In ICU', 'value': 'icu'},
            #{'label': 'On Ventilator', 'value': 'ventilators'},
            #{'label': 'Tests', 'value': 'tests'}
        ]
    else:
        options=[
            {'label': 'Confirmed Cases', 'value': 'cases'},
            {'label': 'Deaths', 'value': 'deaths'}
        ]  
    return options

@app.callback(Output("state-trends-stash", "data"), 
    [
        Input("date-slider", "value"), 
        Input("radio-scaling", "value"),
        Input("radio-current-vs-cumulative", "value"),
        Input("radio-field", "value")
    ]
)
def update_state_trends(days_since_start_of_2020,scaling,current_vs_cumulative,field):
    return gen_state_trend_plot(days_since_start_of_2020,scaling,current_vs_cumulative,field)

# @app.callback(Output("state-trends", "figure"), [Input("state-trends-stash", "data")])
# def plot_state_trends(figure):
#     return figure

@app.callback(Output("state-trends", "figure"), 
    [Input("choropleth", "hoverData"), Input("state-trends-stash", "data")],
    [    
        State("choropleth", "figure"), 
        State("date-slider", "value"), 
        State("radio-scaling", "value"),
        State("radio-current-vs-cumulative", "value"),
        State("radio-field", "value"),
    ]
)
def hover_update_state_trends(hover_data,original_figure,current_figure,days_since_start_of_2020,scaling,current_vs_cumulative,field):
    return update_state_trend_plot(hover_data,original_figure,current_figure,days_since_start_of_2020,scaling,current_vs_cumulative,field)

@app.callback(Output("state-history", "figure"), [Input("choropleth", "hoverData"), Input("date-slider", "value")])
def gen_state_history_plot(hover_data,date):
    #todays_date = pd.datetime(2020,5,3)
    #days_into_year = (todays_date - pd.datetime(2020,1,1)).days
    #lockdown = (pd.datetime(2020,3,11) - pd.datetime(2020,1,1)).days
    selected_date = (pd.datetime(2020,1,1)+timedelta(days=date))
    try:
        state = hover_data['points'][0]['location']
    except:
        state = 'US'

    df = history_df
    data = []
    for year in [2017,2018,2019,2020]:
        sdff = df[(df['year']==year) & (df['Code']==state)]
        #sdff = dff.sort_values(by='days_into_year')
        if year == 2020:
            if (state in ['AK','CT','LA','NC','OH','VA','WV']):
                trim = -5
            else:
                trim = -2
            color='red'
        else:
            color='gray'
            trim = -1
        #data.append(go.Scatter(x=sdff['datetime'].values[0:trim], y=sdff['daily_deaths_per_hundred_thousand'].values[0:trim], mode='lines', line=dict(color=color), name=year))
        data.append(go.Scatter(x=sdff['days_into_year'].values[0:trim], y=sdff['daily_deaths_per_hundred_thousand'].values[0:trim], mode='lines', line=dict(color=color), name=year))
    #data.append(go.Scatter(x=[selected_date,selected_date], y=[0,10], line=dict(color='blue', width=2), opacity=0.2, mode='lines', name=selected_date.strftime('%Y-%m-%d')))
    data.append(go.Scatter(x=[date,date], y=[0,10], line=dict(color='blue', width=2), opacity=0.2, mode='lines', name=selected_date.strftime('%Y-%m-%d')))
    #data.append(go.Scatter(x=typical_df['datetime'], y=typical_df[state+'_typical_plus_covid_daily_deaths_per_hundred_thousand'], mode='lines', line=dict(color='green'), name='Covid'))
    data.append(go.Scatter(x=typical_df.index, y=typical_df[state+'_typical_plus_covid_daily_deaths_per_hundred_thousand'], mode='lines', line=dict(color='green'), name='Covid'))
    #layout = go.Layout(xaxis={"title":"Date"}, yaxis={"title":"Daily Deaths per 100,000 People\nin "+state, "range":[0,10]})
    layout = go.Layout(xaxis={"title":"Day of the Year"}, yaxis={"title":"Daily Deaths per 100,000 People\nin "+state, "range":[0,10]})
    return {"data" : data, "layout" : layout}

if __name__ == '__main__':
    app.run_server(debug=True)