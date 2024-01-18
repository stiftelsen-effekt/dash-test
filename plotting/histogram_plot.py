import numpy as np
import pandas as pd
import plotly.graph_objects as go
import database_import as dbi

df = dbi.get_df(table_name='Donations', database='EffektDonasjonDB')
df = df.sort_values(by='timestamp_confirmed')
df.index = pd.to_datetime(df['timestamp_confirmed'])

# Filter out recurring donations
ID_num_count = df['Donor_ID'].value_counts()
recurring_IDs = [ind for ind,val in zip(ID_num_count.index, ID_num_count.values) if val>1]
df_recurring = df.loc[df['Donor_ID'].isin(recurring_IDs)]

#Get monthly donations for all, and recurring donations
MDs = pd.DataFrame() #monthly donations
MDs['sum_confirmed'] = df['sum_confirmed'].resample('M').sum() #Resample by day
MDs['date_name'] = [ts.month_name()[:3] + ' ' + str(ts.year) for ts in MDs.index]
MDs['timestamp'] = MDs.index
MDs.index = [i for i in range(0,len(MDs))]

MDs_recurring = pd.DataFrame() #monthly donations
MDs_recurring['sum_confirmed'] = df_recurring['sum_confirmed'].resample('M').sum() #Resample by day
MDs_recurring['date_name'] = [ts.month_name()[:3] + ' ' + str(ts.year) for ts in MDs_recurring.index]
MDs_recurring['timestamp'] = MDs_recurring.index
MDs_recurring.index = [i for i in range(0,len(MDs_recurring))]

def get_df_subset_by_month(month_index_range, month_df, full_df):
    all_dates = month_df.iloc[month_index_range[0]:month_index_range[1]]
    date_1 = all_dates['timestamp'].iloc[0]
    date_2 = all_dates['timestamp'].iloc[-1]
    df_subset = full_df.loc[(full_df.index>date_1)&(full_df.index<date_2)]
    return df_subset

def get_histogram(month_index_range, exclude_otd, n_bins=50):
    month_df = MDs_recurring if exclude_otd else MDs
    full_df = df_recurring if exclude_otd else df
    df_subset = get_df_subset_by_month(month_index_range, month_df=month_df, full_df=full_df)
    donations = df_subset['sum_confirmed'].to_numpy()
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x = donations, 
            nbinsx = n_bins, 
            #xbins = dict(start=0, end=max(donations)*1.02, size=max(donations)/50),
            xbins = dict(start=0),
            autobinx=False,
            marker_color = 'black', 
            hovertemplate = '<b>Donasjonsmenge:</b> %{x} NOK<br><b>Antall:</b> %{y:.0f}<extra></extra>', 
            histnorm = ''
    ))
    
    upper_range = int(np.ceil(np.log10(len(donations)))) #Highest power of 10
    major_ticks = np.logspace(0,upper_range,upper_range+1)
    all_ticks = np.outer(major_ticks,np.arange(1,10,1)).flatten()
        
    [fig.add_hline(y=hlv, line_color='#fafafa', line_width=0.5) for hlv in major_ticks]
    fig.update_layout(
        xaxis = dict(title=dict(text='Donasjonsmenge [NOK]'), fixedrange=True),
        yaxis = dict(
            type='log',
            title=dict(text='Antall donasjoner'),
            fixedrange=True, #Disabling zoom
            ticks = 'outside',
            tickvals = all_ticks,
            ticktext = [val if val in major_ticks else '' for val in all_ticks],
            range = [-0.6,upper_range+0.2],
            showgrid=False
            ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="ESKlarheit",
        margin=dict(l=0, r=0, t=0, b=0),
        bargap=0.05
    )
    return fig

