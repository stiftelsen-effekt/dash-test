from dash import Dash, html, dcc, Output, Input, no_update, callback
import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotting.budgets_plot as plot

dash.register_page(__name__)

year_range = (2016,2022)

graph = dcc.Graph(
    id='budget-graph', 
    figure=plot.plot_sankey(year=year_range[0]),
    config={'displayModeBar': False},
    clear_on_unhover=True,
    style={"width": "100%"},
)

slider = dcc.Slider(
    id='year-slider',
    min=year_range[0],
    max=year_range[1],
    marks = {year: str(year) for year in range(year_range[0],year_range[1]+1)},
    step=1,
    included=False
)

year_dropdown = dcc.Dropdown(
    id='year-dropdown', 
    options={year: year for year in range(year_range[0],year_range[1]+1)},
    value=year_range[0],
    clearable=False
)

layout = html.Div(
    dbc.Container([
        #slider,
        dbc.Row(dbc.Col(year_dropdown, width=2)),
        html.Br(),
        dbc.Row(dbc.Col(graph)),
        ], fluid=True, style={"width": "100%", "max-width":"900px", 'margin':0})#, style={'backgroundColor':'#fafafa'})
)

@callback(
    Output('budget-graph','figure'),
    #Input('year-slider','value')
    Input('year-dropdown','value')
)
def update_graph(year):
    if year==None:
        return no_update
    return plot.plot_sankey(int(year))
