from dash import Dash, html, dcc, Output, Input, callback
import dash
import dash_bootstrap_components as dbc
import plotting.histogram_plot as hp

dash.register_page(__name__)

month_marks = {i: ts.month_name()[:3] + ' ' + str(ts.year) for i,ts in enumerate(hp.MDs['timestamp'])}

onetime_donations_switch = dbc.Switch(id='onetime-donations-switch',label='Eksluder enkeltdonasjoner', value=False)

month_slider = dcc.RangeSlider(
    id='month-slider', 
    marks=None, 
    value=[0,len(month_marks)-1],
    step=1,
    min=0,
    max=len(month_marks)-1,
    allowCross= False,
    pushable=12, 
)

histogram_graph = dcc.Graph(
    id='histogram-graph', 
    config={'displayModeBar': False}, #Hide options for saving graph, zooming etc
    style={"width": "100%", "max-width":"1000px"},
)

layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.Span(month_marks[0], id='from-month'), width=1),
            dbc.Col(month_slider, width=5, style={'padding':'0px 0px 0px'}),
            dbc.Col(html.Span(month_marks[len(month_marks)-1], id='to-month'), width=1),
            dbc.Col(onetime_donations_switch,  width={'size':4,'offset':1}),
        ], align='center', justify='start'), #style = {"height": "100%", 'background-color':'yellow'}), 
        dbc.Row(dbc.Col(histogram_graph)),
        ], style={"width": "100%", "max-width":"900px", 'margin':0})

@callback(
    Output('histogram-graph','figure'),
    Input('month-slider','value'),
    Input('onetime-donations-switch','value'),
    prevent_inital_callback=True
)
def update_histogram(month_index_range, exclude_otd):
    return hp.get_histogram(month_index_range, exclude_otd=exclude_otd)

@callback(
    Output('from-month','children'),
    Output('to-month','children'),
    Input('month-slider','value')
)
def update_date_text(month_range):
    return str(month_marks[month_range[0]]), str(month_marks[month_range[1]])
    