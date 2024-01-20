from dash import html
import dash
import dash_bootstrap_components as dbc
import database_import as dbi

dash.register_page(__name__)

number_style = {"font-size":40,"width": "100%", 'margin':0, 'text-align': 'center'}
df = dbi.get_df(table_name='Donations')

layout = html.Div(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([len(df['Donor_ID'].unique())], style=number_style),
                html.Div(['Unike givere'], style={'text-align': 'center'})
            ], width=4),
            dbc.Col([
                html.Div([f'{df["Sum_confirmed"].sum():,.0f} kr'], style=number_style),
                html.Div(['Donert'], style={'text-align': 'center'})
            #], width=4, style={'border-left': '2px solid black','border-right': '2px solid black'}),
            ], width=4),
            dbc.Col([
                html.Div([len(df.index)], style=number_style),
                html.Div(['Donasjoner'], style={'text-align': 'center'})
            ], width=4)
        ], justify="center")
    ], fluid=True, style={"width": "100%", "max-width":"1000px", 'margin':0})
)
