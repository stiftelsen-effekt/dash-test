from dash import Dash, html, dcc, Output, Input, no_update, callback
import dash_bootstrap_components as dbc
import plotting.organizations_plot as pl
import numpy as np
import dash

dash.register_page(__name__)

org_descriptions = {
    'AMF': dict(descr='Forebygger dødsfall fra malaria.', link='https://www.againstmalaria.com/'),
    'Drift': dict(descr='Donasjoner til drift av gieffektivt.no', link='https://gieffektivt.no/'),
    'GD': dict(descr='Sender kontantoverføringer til ekstremt fattige i Kenya og Uganda.', link='https://www.givedirectly.org/'),
    'TCF': dict(descr='Givewell beskrivelse', link='https://www.givewell.org/'),
    'HKI': dict(descr='Forebygger mangelsykdommer med tilskudd av A-vitamin.', link='https://helenkellerintl.org/'),
    'SCI': dict(descr='SCI beskrivelse', link='https://unlimithealth.org/'),
    'NI': dict(descr='Vaksinerer spedbarn i Nigeria.', link='https://www.newincentives.org/')
}

graph = dcc.Graph(
    id='yearly-donations-graph', 
    figure=pl.get_plot(),
    config={'displayModeBar': False},
    clear_on_unhover=True,
    style={"width": "100%", "max-width":"900px"},
)

layout = html.Div(
    dbc.Container([
        dbc.Row(dbc.Col(graph)),
        dcc.Tooltip(id='graph-tooltip', direction='right', show=False, style={'backgroundColor':'#fafafa'}),
    ]), style={'margin': '50px 0px 0px'}
)

@callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("yearly-donations-graph", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update
    
    point = hoverData["points"][0]
    trace_number = point['curveNumber']

    image_trace = (trace_number-3)%7==0 #Boolean for whether highlighted point is a trace with image (col 1)
    text_trace = (trace_number-5)%7==0 #Boolean for whether highlighted point is a trace with org names (col 2)
    time_trace = (trace_number-6)%7==0 #Boolean for whether highlighted point is a trace with time vs donations (col 3)
    if not image_trace and (not time_trace if pl.tooltip else True):
        return False, no_update, no_update
    
    org_id = int(np.floor((trace_number-3)/7))
    org_name = pl.sorted_orgs[org_id]
    org_full_name = pl.abbriv2fullname_dict[org_name]
    bbox = point["bbox"]
   
    if image_trace or text_trace:
        org_text = pl.df_fullnames[pl.df_fullnames['abbriv']==org_name]['short_desc'].values[0]
    else:
        point_number = point['pointNumber']
        org_text = f'''
        Dato: {pl.days_by_org[org_id][point_number].strftime("%d-%m-%Y")} \n
        Mengde: {np.cumsum(pl.donations_by_org[org_id])[point_number]:,.0f} kr'''
    
    children = [
        html.Div(
            dbc.Container([
                html.Img(src=f'assets/black horizontal logos/{org_name}.png', style={"width": "80%"}),
                html.Hr(),
                html.P(f"{org_text}"),
                #dcc.Link(href=org_descriptions[org_name]['link'], style={'color':'black'})
                ], 
                style={'width':'400px','white-space': 'normal'}
            )
        )]
    return True, bbox, children