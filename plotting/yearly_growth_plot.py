import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database_import as dbi
pd.set_option("display.precision", 0)

def fixLeapYear(dates,donations):
    isNotLeapYearDate = ~(dates=='02-29')
    return dates[isNotLeapYearDate],donations[isNotLeapYearDate]

# df = pd.read_csv('donations-effekt.csv', parse_dates=['Timestamp_confirmed'])
# df = df.sort_values(by='Timestamp_confirmed')
df = dbi.get_df(table_name='Donations')
# df = dbi.ds_corr.sort_values(by='Timestamp_confirmed')
df = df.sort_values(by='Timestamp_confirmed')
df.index = pd.to_datetime(df['Timestamp_confirmed'])

# Filter out recurring donations
ID_num_count = df['Donor_ID'].value_counts()
recurring_IDs = [ind for ind,val in zip(ID_num_count.index, ID_num_count.values) if val>1]
df_reccuring = df.loc[df['Donor_ID'].isin(recurring_IDs)]

# Get yearly donations and sort by year
DDs = pd.DataFrame() #daily donations
DDs['value'] = df['Sum_confirmed'].resample('D').sum() #Resample by day
DDs['y-m-d'] = pd.to_datetime(DDs.index)
DDs['y']= DDs['y-m-d'].dt.strftime('%Y')
DDs['m-d'] = DDs['y-m-d'].dt.strftime('%m') + "-" + DDs['y-m-d'].dt.strftime('%d')

year_strings = [str(yr) for yr in range(2018,int(DDs['y'][-1])+1)]
dates_by_year     = [ DDs.loc[DDs['y']==year_str,'m-d'].to_numpy() for year_str in year_strings]
donations_by_year = [ DDs.loc[DDs['y']==year_str,'value'].to_numpy() for year_str in year_strings]
dates_by_year,donations_by_year = zip(*[ fixLeapYear(dts,dons) for dts,dons in zip(dates_by_year,donations_by_year) ])

yMax = max([sum(dons) for dons in donations_by_year])

yearly_dons_hovertemplate = '<b>Dato:</b> %{x}<br><b>Verdi:</b> %{y:,.0f} kr'
def get_yearly_donations_plot():
    fig = go.Figure()
    for dates, dons, year_str in zip(dates_by_year, donations_by_year, year_strings):
        dates = ['1970-'+d for d in dates]
        dash = 'dot' if year_str==year_strings[-1] else 'solid'
        dons_cumsum = np.cumsum(dons)
        fig.add_trace(
            go.Scatter(x=dates, y=dons_cumsum, line=dict(color='black', width=2, dash=dash), name=year_str, xhoverformat="%d %b", hovertemplate=yearly_dons_hovertemplate)
        )
        fig.add_trace(
            go.Scatter(x=[dates[-1]], y=[dons_cumsum[-1]], name=year_str, mode='markers',  marker=dict(color='black'), xhoverformat="%d %b", hovertemplate=yearly_dons_hovertemplate, cliponaxis=False)
        )
        fig.add_annotation(
            x=dates[-1], y=dons_cumsum[-1], text=year_str, showarrow=False, font=dict(color='black'), xanchor='left', xshift=5, bgcolor='#fafafa'
        )
    fig.update_layout(
        xaxis = dict(
            tickformat = '%b',
            dtick="M1", 
            ticklabelmode="period", 
            ticks='outside', 
            range = ['1970-01-01','1971-01-01'],
            showgrid=False,
            zeroline=True,
            #showline=True,
            linecolor='black',
            fixedrange=True, #Disabling zoom
        ),
        yaxis = dict(
            gridcolor='black',
            gridwidth=0.5, 
            fixedrange=True, 
            rangemode = "tozero"
        ), #Disabling zoom),
        hoverlabel=dict(bgcolor="#fafafa"),
        showlegend = False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        # paper_bgcolor='#fafafa',
        # plot_bgcolor='#fafafa',
        font_family="ESKlarheit",
        margin=dict(l=0, r=40, t=0, b=0),
    )
    # target=32_000_000
    # fig.add_hline(y=target)
    # fig.add_annotation(
    #         x='1970-07-01', y=target, text='Mål 2023', showarrow=False, font=dict(color='black'), xanchor='center', xshift=0, bgcolor='#fafafa'
    #     )
        #plt.plot(dates[-1], dons_cumsum[-1], color=color_, marker='.', markersize=10)
        #txtBox = plt.text(dates[-1], dons_cumsum[-1] + 0.02*yMax, year_str, va='bottom',ha='center')
    return fig

