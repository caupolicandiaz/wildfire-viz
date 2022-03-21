# -*- coding: utf-8 -*-
# dash imports
import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import plotly
import plotly.express as px
import plotly.graph_objs as go
import plotly.figure_factory as ff
import colorlover as cl

import pandas as pd
import numpy as np
import re
import pickle
#from config import api_key

external_stylesheets = ['/assets/dash_style_sheet_fire.css',] 

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

mapbox_access_token = api_key

# add data
with open('dataframes.pkl','rb') as f:
    data_dict = pickle.load(f)


df = data_dict['main']

# stacked area chart data
fire_counts = data_dict['counts']

# acres burned data
acres = data_dict['acres'] 

# create options list
fire_causes = list(df['general_cause'].unique())
dropdown_lst = [{'label':x,'value':x} for x in fire_causes]

# create color scales
rgb_colors = px.colors.sequential.Burg                  #original burgandy scale
ten_colors = cl.to_rgb(cl.interp(rgb_colors,10))        #scale extended


def add_alpha(a_lst, pct):
    out = []
    for elem in a_lst:
        values = re.split(r'\(|\)',elem)[1]
        out.append(f'rgba({values},{pct})')
    return out

alpha_colors = add_alpha(ten_colors,'.9')               #scale translated to include alpha


# chart definitions ######################################

def plot_styling(func):
    def update_styling(*args, **kwargs):
        new_plot = func(*args, **kwargs).update_layout(plot_bgcolor='#ececf1', paper_bgcolor='#ececf1', autosize=True)
        return new_plot
    return update_styling

@plot_styling
def bar_fig(years_data,scale_choice):
    data = list(acres['total_acres'].iteritems())
    year_selection = list(range(years_data[0],years_data[1] + 1))

    hover_format = 'Year: %{x}<br>' + 'Total Acres: %{y:.3s}<extra></extra>'
    acres_fig = go.Figure()

    acres_fig.add_trace(go.Bar(
        x=acres.index,
        y=[x[1] if x[0] in year_selection else np.nan for x in data],
        marker_color='rgba(152, 103, 144,.9)',
        hovertemplate = hover_format,))
    acres_fig.add_trace(go.Bar(
        x=acres.index,
        y=[x[1] if x[0] not in year_selection else np.nan for x in data],
        marker_color='rgba(152, 103, 144,.4)',
        hovertemplate = hover_format,))
    acres_fig.update_layout(barmode='stack', showlegend=False, autosize=True)  
    acres_fig.update_xaxes(title='Years')
    acres_fig.update_yaxes(title='Acres Burned',type=scale_choice)

    return acres_fig


@plot_styling
def stacked_fig(dd_selection):
    go_stack = go.Figure()
    col_lst = fire_counts.columns
    selected = dd_selection
    fade = [] if not selected else [x for x in col_lst if x not in selected] 

    the_color_scale = \
    [alpha_colors[i] if x not in fade else re.sub(r'[\d.]+\)','.2)',alpha_colors[i]) for i, x in enumerate(col_lst)]

    for i, col in enumerate(col_lst):

            go_stack.add_trace(go.Scatter(
                x=fire_counts.index, y=fire_counts[col], name=col,
                fillcolor= the_color_scale[i],
                hovertemplate =
                f"Source: {col} <br>" 
                + "Year: %{x} <br>" 
                + "Total Fires: %{y} <br>"
                + "<extra></extra>",
                showlegend=False,
                mode='lines',
                line=dict(width=0, color= the_color_scale[i]),
                stackgroup='one', 
            ))

    go_stack.update_yaxes(title='Annual Fire Counts', tickvals=list(range(500,2500,500)), showgrid=True, automargin=True)
    go_stack.update_xaxes(title='Years', showgrid=False)

    return go_stack


@plot_styling
def scatter_map(the_data):

    sub = pd.read_json(the_data)

    scatter_fig = go.Figure()

    customdf = np.stack((sub['general_cause'],sub['fire_year'],sub['total_acres']),axis=-1)

    scatter_fig.add_trace(go.Scattermapbox(
            lat=sub['latitude'],
            lon=sub['longitude'],
            showlegend=True,
            name='',
            mode='markers',
            customdata = customdf,
            hovertemplate = 'Source: %{customdata[0]} <br> Year: %{customdata[1]} <br> Total Acres: %{customdata[2]:,.0f} <br>',
            marker=go.scattermapbox.Marker(
                size=10, 
                color='#986790',
                opacity=.5,
            ),
        ))

    scatter_fig.update_layout(
        hovermode='closest',
        legend=dict(
            orientation="v",
            title="Fires",
            itemsizing="constant",
            ),
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=44.0,
                lon=-120.5
            ),
            pitch=0,
            zoom=5
        ),
    )

    return scatter_fig

app.layout = html.Div(className='grid-page',children=[
    html.Div(
        className='flex-header',
        id='banner-container',
        children=[
        html.P(className='banner-txt', children='Oregon Wildfires: Exploring 50 Years of Data'),
        html.H3(' '),
    ]),
    html.Div(id='side-bar',children=[
        dcc.Tabs(value='tab-1', children=[
            dcc.Tab(label='Visualization Controls', value='tab-1')]),
        html.Div(className='flex-header', id='cat-header',children=[
            html.P('Ignition Sources'),
            html.Button('Reset Values',id='reset-button'),
            dcc.Store(id='click-value',data=0)]),
        html.Div(id='dd-container',children=dcc.Dropdown(
            id='filter-dd',
            options=dropdown_lst,
            value=fire_causes,
            placeholder="Select a cause",
            multi=True),),
        html.Div(className='flex-header',id='range-header',children=[
            html.P('Year Range: '),
            html.Div(id='range-text'),]),  
        dcc.RangeSlider(
            className='the-slider',
            id='year-selector',
            marks={i: {'label':'{}'.format(i), 'style':{'color': 'rgba(0, 0, 0, 0.6)'}} \
                    for i in range(1970, 2030, 10)},
            min=1970,
            max=2020,
            value=[2010,2020],
            step=1), 
        html.Div(className='flex-header',id='acre-header',children=[
            html.P('* Fire Size (Acres): '),
            html.Div(id='acre-text'),]), 
        dcc.RangeSlider(
            className='the-slider',
            id='size-selector',
            marks={i: {'label':'{}'.format(10 ** i), 'style':{'color': 'rgba(0, 0, 0, 0.6)'}} \
                    for i in range(5)},
            value=[2,3], 
            step=.01),
        html.Div(className='flex-header', id='bubble-header',children=[
            html.P('Filter Summary: '),
            ]),
        html.Div(id='map-data'),
        html.Br(),
        html.P('* A selection that contains the max acre range will display all fires above this value as well'),
        dcc.Markdown(
            '''
            Source: [Kaggle Datasets](https://www.kaggle.com/fritzstevenson/oregons-historical-wildfires)   
            Code: [Git Repo](https://github.com/caupolicandiaz/wildfire-viz)
            '''
            ),
        ]),
    html.Div(id='main-figure',children=[
        dcc.Tabs(
            id='tabs-main',
            value='tab-1',
            className='main-tab-frame',
            children=[
                dcc.Tab(
                    label='Annual Fire Counts',
                    value='tab-1',
                    className='custom-frame',
                    selected_className='selected-frame',children=[
                        html.Div(className='plot-header', children='Fire Chart'),
                        dcc.Graph(
                        id='fire-fig',
                    ),]),
                dcc.Tab(
                    label='Total Acres Burned',
                    value='tab-2',
                    className='custom-frame',
                    selected_className='selected-frame',children=[
                        html.Div(className='flex-header', id='scale-container',children=[
                            html.Div(id='y-label', children='Y-scale:  '),
                            dcc.RadioItems(id='radio-scale',
                                options=[
                                    {'label': 'log', 'value': 'log'},
                                    {'label': 'linear', 'value': 'linear'},
                                ],
                                value='log',
                                labelStyle={'display': 'inline-block'}
                            ),]), 
                        dcc.Graph(
                            id='acres-fig',
                        ),]),
                dcc.Tab(
                    label='Fire Map',
                    value='tab-3',
                    className='custom-frame',
                    selected_className='selected-frame',children=[
                        html.Div(className='plot-header', children='Oregon Map'),
                        dcc.Graph(
                            id='oregon-map',
                        ),]),
              ])]),
    dcc.Store(id='intermediate-value'),
    dcc.Store(id='transformed-value'),
    html.Div(className='footer', children=[ 
        html.Div(''), 
        html.Div(id='text-out'), 
        ]),
])


########################################################################################################
########################################################################################################
# app call back section 


@app.callback(Output('intermediate-value', 'data'), 
    [Input('year-selector', 'value'),
    Input('filter-dd', 'value'),
    Input('transformed-value', 'data')])

def clean_data(value, category, sizes):
     # a clean data step

     years_rng = [value[0]] if value[0] == value[1] else list(range(value[0],value[1] + 1,1))
     years_criteria = df['fire_year'].isin(years_rng)  
     
     category = [category] if isinstance(category,str) else category
     category_criteria = df['general_cause'].isin(category) 

     max = df['total_acres'].max() if sizes[1] == 10000 else sizes[1]
     size_criteria = df['total_acres'].between(sizes[0], max)

     all_criteria = years_criteria & category_criteria & size_criteria
     
     cleaned_df = df[all_criteria]

     return cleaned_df.to_json()

# transform func
def transform_value(value):
    return int(10 ** value)

@app.callback(Output('transformed-value', 'data'), 
    [Input('size-selector', 'value')],
    )

def update_sizes(orig_sizes):
    
    return [transform_value(x) for x in orig_sizes]

# bar chart call back
@app.callback(
    Output('acres-fig', 'figure'), 
    [Input('year-selector', 'value'),
    Input('radio-scale', 'value')],
    )

def update_bars(the_years,the_scale):
       
    return bar_fig(the_years,the_scale)


# stacked area call back
@app.callback(
    Output('fire-fig', 'figure'), 
    [Input('filter-dd', 'value')],
    )

def update_fig(selection):
    if selection == None:

        raise PreventUpdate
    else:
       
        return stacked_fig(selection)

# map functions
@app.callback(
    Output('oregon-map', 'figure'), 
    [Input('intermediate-value', 'data')],
    )

def update_map(jsonified_data):
       
    return scatter_map(jsonified_data)

# year slider output
@app.callback(
    Output('range-text', 'children'), 
    [Input('year-selector', 'value')],
    )

def update_range(some_text):

    if some_text == None:
        return []
    else:
        return f'{some_text[0]} - {some_text[1]}'

# acre slider output
@app.callback(
    Output('acre-text', 'children'), 
    [Input('transformed-value', 'data')],
    )

def update_acres(some_text):

    if some_text == None:
        return []
    else:
        return f'{some_text[0]} - {some_text[1]}'

# map view summary
@app.callback(
    Output('map-data', 'children'), 
    [Input('intermediate-value', 'data')],
    )
def update_map_totals(some_data):

    if some_data == None:
        raise PreventUpdate
    else:
        temp_df = pd.read_json(some_data)
        the_count = temp_df['id'].count()
        the_acres = round(temp_df['total_acres'].sum(),0)
        return [html.P('Total Fires: {:,}'.format(the_count)) ,
                html.P('Total Acres: {:,.0f}'.format(the_acres))]


# reset dropdown field
@app.callback(
    Output('filter-dd', 'value'), 
    [Input('reset-button', 'n_clicks'),
    Input('click-value', 'data')],
    )
def update_dropdown(clicks,tally):

    if clicks == tally:
        return PreventUpdate
    else:
        return fire_causes


# demo callback
@app.callback(
    Output('text-out', 'children'), 
    [Input('intermediate-value', 'data')],
    )
def update_div(some_text):

    if some_text == None:
        return []
    else:
        return " " #output check



if __name__ == '__main__':
    app.run_server(debug=False)
