from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import plotting.yearly_growth_plot as plot

dash.register_page(__name__)

yearly_donations_graph = dcc.Graph(
    id='yearly-donations-graph', 
    figure=plot.get_yearly_donations_plot(),
    config={'displayModeBar': False},
    style={"width": "100%", "max-width":"1000px"}
)

layout = html.Div(
    dbc.Container([
        dbc.Row(dbc.Col(yearly_donations_graph)),
        ])#, style={'backgroundColor':'#fafafa'})
)