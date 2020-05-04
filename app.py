
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


def gen_state_trend_plot(days_since_start_of_2020,scaling,current_vs_cumulative,field, hover_data):
    df = state_df
    try:
        GUI_state = hover_data['points'][0]['location']
    except:
        GUI_state = ''
    data = []
    
    for state in df['state'].unique():
        dfs = df[df['state']==state]
        if state == GUI_state: opacity = 1
        else: opacity = 0.2
        if scaling == 'linear':
            column_string = current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        else:
            column_string = 'log_'+current_vs_cumulative+'_'+field+'_per_hundred_thousand'
        data.append(go.Scatter(x=dfs['datetime'], y=dfs[column_string], mode='lines', name=state, opacity=opacity))
    layout = go.Layout(hovermode='closest', xaxis={"title":"Days since start of 2020"})
    return {"data" : data, "layout" : layout}

def gen_map(date,geography,scaling,current_vs_cumulative,field):
    # TODO: PROBLEM WITH TIME-FILTER!!!!!!!!!
    #datestring = int((start_of_2020+timedelta(days=date)).strftime('%Y-%m-%d'))
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
            zmax = max_value
            #text = df[df['year']==year][radio+' text'],
            #hoverinfo='location+text',
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
            html.P("State trends: Hovering over a state on the map above will highlight the state in the figure below."),
            dcc.Graph(
                id='state-trends'
                #figure=gen_state_trend_plot(radio, '')
            ),
            dcc.Graph(
                id='state-history'
            )
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
        title_string = f'Cumulative {field_string} per 100,000 people'
    else:
        title_string = f'Average Daily {field_string} per 100,000 people over last week'
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

@app.callback(Output("state-trends", "figure"), 
    [
        Input("date-slider", "value"), 
        Input("radio-scaling", "value"),
        Input("radio-current-vs-cumulative", "value"),
        Input("radio-field", "value"),
        Input("choropleth", "hoverData")
    ]
)
def update_state_trends(days_since_start_of_2020,scaling,current_vs_cumulative,field, hover_data):
    return gen_state_trend_plot(days_since_start_of_2020,scaling,current_vs_cumulative,field, hover_data)

if __name__ == '__main__':
    app.run_server(debug=True)