# -*- coding: utf-8 -*-
# dash imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import plotly
import plotly.express as px
import plotly.graph_objs as go
import plotly.figure_factory as ff
import colorlover as cl

import pandas as pd
import numpy as np
import regex as  re

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'\
'/assets/dash_style_sheet_fires.css',]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

mapbox_access_token = 'pk.eyJ1IjoicGF1bGR6IiwiYSI6ImNrNDIxcGVqNTA3ajYzZm8wbXI4Mml6NDIifQ.PWBbtxmT5Fk_EGU90oYVIw'

# add data
df = pd.read_excel('oregon_fires_clean.xlsx',header=0)

# stacked area chart data
fire_counts = df.pivot_table(values='id',index='fire_year',columns='general_cause',aggfunc='count')
fire_counts.drop(columns='Under Invest',inplace=True)

# acres burned data
acres = df.groupby(['fire_year']).sum()

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
    acres_fig.update_layout(barmode='stack',plot_bgcolor='#ececf1',height=350, margin=dict(t=25),showlegend=False,)                           
    acres_fig.update_xaxes(title='Years')
    acres_fig.update_yaxes(title='Acres Burned',type=scale_choice)

    return acres_fig


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
                f"Source: {col}" +
                "<br>Year: %{x}<br>" +
                "Total Fires: %{y}<br>"+  
                "<extra></extra>",
                showlegend=False,
                mode='lines',
                line=dict(width=0, color= the_color_scale[i]),
                stackgroup='one', # define stack group
            ))

    go_stack.update_layout(title_text='',plot_bgcolor='#ececf1',
                           height=600,)
    go_stack.update_yaxes(title='Annual Fire Counts',tickvals=list(range(500,2500,500)),showgrid=True)
    go_stack.update_xaxes(showgrid=False)

    return go_stack


def scatter_map(the_data):

    sub = pd.read_json(the_data)
    markers = [10,100,1000]

    scatter_fig = go.Figure()

    for x in markers:
        temp = sub[sub['marker_sz']==x]

        the_text = 'Source: ' + temp['general_cause'] + '<br>' + 'Year: ' \
        + temp['fire_year'].astype('str') + '<br>' + 'Total Acres: ' \
        + temp['total_acres'].astype('str') 

        scatter_fig.add_trace(go.Scattermapbox(
                lat=temp['latitude'],
                lon=temp['longitude'],
                text=the_text,              
                showlegend=True,
                name=str(x),
                mode='markers',
                hoverinfo='text',
                marker=go.scattermapbox.Marker(
                    size=temp['marker_sz'],
                    sizemode='area',
                    color='#986790', #'#aaadf8',
                    opacity=.5,
                ),
            ))

    scatter_fig.update_layout(
        # autosize=True,
        # width=450,
        height=550,
        hovermode='closest',
        # title_text='Fire Locations',
        paper_bgcolor='#BDD0D0', #rgba(0,0,0,0)',
        legend=dict(
            orientation="v",
            title="Acres",
            itemsizing="constant",
            # yanchor="bottom",
            # y=1.02,
            # xanchor="right",
            # x=1
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
        className='header',
        children=[
        html.H2('Oregon Wildfires: Exploring 50 years of data'),
        html.H3(' '),
    ]),
    html.Div(id='side-bar',children=[
        dcc.Tabs(
            id='tabs-menu',
            value='tab-2',
            className='custom-tab-holder',
            children=[
                dcc.Tab(
                    label='Data',
                    value='tab-1',
                    className='custom-tab',children=[
                        html.P(children='Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod' 
                                'tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,'
                                'quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo'
                                'consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse'
                                'cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non'
                                'proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
                    ),],),
                dcc.Tab( 
                    label='View Controls',
                    value='tab-2',
                    className='custom-tab',children=[
                    html.H3(''),
                    html.Div(id='tab-header',children=[
                        html.P('Ignition Source Filter'),
                        html.Button('Reset Values',id='reset-button'),
                        dcc.Store(id='click-value',data=0)]),
                    html.Div(id='dd-container',children=dcc.Dropdown(
                        id='filter-dd',
                        options=dropdown_lst,
                        value=fire_causes,
                        placeholder="Select a cause",
                        multi=True),),
                    html.Div(id='range-header',children=[
                        html.P('Year Range Filter: '),
                        html.Div(id='range-text'),]),  
                    dcc.RangeSlider(
                        className='the-slider',
                        id='range-selector',
                        marks={i: '{}'.format(i) for i in range(1970, 2025,5)},
                        min=1970,
                        max=2020,
                        value=[2018,2020]), 
                    html.Div(id='bubble-header',children=[
                        html.P('Filter Summary: '),
                        html.Div(id='map-data'),]),                      
                    html.Div(className='bubble-figure',children=[
                        dcc.Graph(
                            id='oregon-map',
                        ),]),
                    
                ]),
        ]),
        ]),    
    html.Div(className='stacked-figure',children=[
        dcc.Graph(
            id='fire-fig',
        ),]), 
    html.Div(className='bar-figure',children=[
        html.Div(id='scale-container',children=[
            html.Div(id='scale-title',children='Y-scale:  '),
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
    dcc.Store(id='intermediate-value'),
    html.Div(className='footer', children=[ 
        html.Div(''), 
        html.Div(id='text-out'), 
        ]),
])


########################################################################################################
########################################################################################################
# app call back section 
@app.callback(Output('intermediate-value', 'data'), 
    [Input('range-selector', 'value'),
    Input('filter-dd', 'value')])
def clean_data(value,category):
     # some expensive clean data step

     years_rng = [value[0]] if value[0] == value[1] else list(range(value[0],value[1] + 1,1))
     category = [category] if isinstance(category,str) else category

     cleaned_df = df[(df['fire_year'].isin(years_rng)) & (df['general_cause'].isin(category))]

     # more generally, this line would be
     # json.dumps(cleaned_df)
     return cleaned_df.to_json() #date_format='iso', orient='split'

# bar chart call back
@app.callback(
    Output('acres-fig', 'figure'), 
    [Input('range-selector', 'value'),
    Input('radio-scale', 'value')],
    )

def update_bars(the_years,the_scale):
    # if the_years == None and the_scale == None:

    #     raise PreventUpdate
    # else:
       
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
    if jsonified_data == None:

        raise PreventUpdate
    else:
       
        return scatter_map(jsonified_data)

# slider output
@app.callback(
    Output('range-text', 'children'), 
    [Input('range-selector', 'value')],
    )
def update_range(some_text):

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
        return html.H5('Fires: {:,} , Total Acres: {:,.0f}'.format(the_count, the_acres))


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
    [Input('radio-scale', 'value')],
    )
def update_div(some_text):

    if some_text == None:
        return []
    else:
        return str(some_text)



# if __name__ == '__main__':
#     app.run_server(debug=False)