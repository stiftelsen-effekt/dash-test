import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd
import numpy as np
import database_import as dbi
from datetime import timedelta, datetime

tooltip = False
include_givewell = True
include_number = 6 #Number of orgs to include
sparkline = True
hover_template = '<b>Dato:</b> %{x}<br><b>Verdi:</b> %{y:,.0f} kr'

def add_image_trace(fig, org, row, col=1):
    # Image column 
    fig.add_layout_image(
        dict(
            source=f'assets/black horizontal logos/{org}.png',
            #source=f'assets/Black and white logos/New Incentives black.svg',
            xref="x domain",
            yref="y domain",
            xanchor="left", yanchor="middle",
            x=0, y=0.5,
            sizex=1,
            sizey=1,
            sizing="contain",
        ),
        row=row, col=col
    )
    fig.add_trace( #Trace 6n+3
        go.Scatter(
                x=[0,4,4,0,0], #Add transparent trace for hover info
                y=[0,0,4,4,0],
                fill='toself',
                fillcolor='rgba(255,0,0,0.0)',
                line=dict(color='rgba(255,0,0,0.0)'),
                mode='lines',
                name=None,
                hoverinfo=None
                ), 
    row=row, col=col)
    fig.update_xaxes(range=[0,4],row=row, col=col)
    return fig

def add_name_trace(fig, org, row, col=2):
    # Name column
    fig.add_trace(
        go.Scatter(
            x=[0.0],y=[0.5], text=abbriv2fullname_dict[org], mode='text',textposition='middle right', hoverinfo=None
        ), row=row, col=col
    )
    fig.add_trace( #Trace 6n+5
        go.Scatter(
            x=[0,1,1,0,0], #Add transparent trace for hover info
            y=[0,0,1,1,0],
            fill='toself',
            fillcolor='rgba(255,0,0,0.0)',
            line=dict(color='rgba(255,0,0,0.0)'),
            mode='lines',
            name=None,
            hoverinfo=None
            ), row=row, col=col
    )
    #fig.add_trace(go.Scatter(x=[0.5],y=[0.5], mode='none', hoverinfo=None), row=j, col=2) #Add for hover tooltip
    fig.update_xaxes(range=[0,1],row=row, col=col)
    return fig

def add_donation_trace(fig, org, row, col=3):
    dates = df.loc[df['Org']==org,'day'].to_numpy()
    donations = df.loc[df['Org']==org,'Amount'].to_numpy()
    # Sparkline column
    if sparkline:
        fig.add_trace( #Trace 6n+6
            go.Scatter(
                    x=dates,
                    y=np.cumsum(donations), 
                    mode='lines', 
                    line=dict(color='black'), 
                    visible=True,
                    name=abbriv2fullname_dict[org],
                    xhoverformat="%d %b %Y",
                    hovertemplate=hover_template
                    ),row=row, col=col
        )
        fig.add_trace(
            go.Scatter(
                x=[dates[0], dates[-1]], 
                y=[np.cumsum(donations)[0],np.cumsum(donations)[-1]],
                mode='markers',
                marker=dict(color='black'),
                hovertemplate=hover_template,
                name=abbriv2fullname_dict[org],
                xhoverformat="%d %b %Y",
                cliponaxis=False, #In order for markers not to be cut
                ), row=row, col=col
            
            )
        fig.update_xaxes(range=[min_date,max_date],row=row, col=col) #Use instead of share_xaxes because that hides traces for some reason
    else:
        org_df = df_year.loc[df_year['Org']==org]
        fig.add_trace( #Trace 6n+6
            go.Bar(
                    x=org_df['year'],
                    y=org_df['Amount'],
                    #marker_color=['grey' if year==datetime.now().year else 'black' for year in org_df['year']],
                    marker_color='black',
                    #textposition="outside",
                    #texttemplate='%{y:.0f}', 
                    visible=True,
                    name=abbriv2fullname_dict[org],
                    xhoverformat="%d %b %Y",
                    hovertemplate='<b>År:</b> %{x}<br><b>Verdi:</b> %{y:,.0f} kr'
                    ),row=row, col=col
        )
        fig.add_trace(go.Scatter(x=[np.nan],y=[np.nan])) #Empty plot for trace order to be correct
        
        fig.update_xaxes(range=[min(df_year['year'])-0.5,max(df_year['year'])+0.5],row=row, col=col) #Use instead of share_xaxes because that hides traces for some reason
        fig.update_yaxes(range=[0,1.5*max(org_df['Amount'])],row=row, col=col)
    return fig

def add_histogram_trace(fig, org, row, col=4):
    donations = df.loc[df['Org']==org,'Amount'].to_numpy()
    fig.add_trace(
            go.Scatter(
                x=[0, 0, sum(donations), sum(donations), 0],
                y=[1,-1,-1,1,1], 
                mode='lines', 
                line=dict(color='black'), 
                fill='toself', 
                fillcolor='black')
            ,row=row, col=col)
    fig.add_trace(
        go.Scatter(
            x=[sum(donations)+0.02*max_total_donation] ,
            y=[0], 
            mode='text', 
            text=f'{np.cumsum(donations)[-1]/1e6:.3f}', 
            textposition='middle right',
            cliponaxis=False,
            ), row=row, col=4)
    fig.update_xaxes(range=[0,max_total_donation*1.25],row=row, col=col)
    fig.update_yaxes(range=[-1.1,1.1],row=row, col=col)
    return fig

#df = pd.read_csv('summary.csv')
#df = dbi.get_df()
df = dbi.get_df(table_name='Scorecard_Organization_donations')
df.index = pd.to_datetime(df['Timestamp']).dt.date
df['day'] = df.index
df = df.sort_values(by='day')
df['year'] = df['Timestamp'].dt.year
df_year = df.groupby(['year', 'Org'])['Amount'].sum().reset_index()

df_fullnames = pd.read_csv('organizations.csv')#, encoding='latin1')
#df_fullnames = dbi.org_df
abbriv2fullname_dict = {abbriv: fullname for abbriv, fullname in zip(df_fullnames['abbriv'],df_fullnames['full_name'])}

all_unique_org_names = df['Org'].unique()

unique_org_names = all_unique_org_names if include_givewell else all_unique_org_names[(all_unique_org_names!='GiveWell')]
total_sums = [df.loc[df['Org']==orgName]['Amount'].sum() for orgName in unique_org_names]
sorted_index = np.argsort(total_sums)

#sorted_orgs = unique_org_names[sorted_index]
sorted_orgs = unique_org_names[sorted_index][len(all_unique_org_names)-include_number:]
# days_by_org = [ df.loc[df['Org']==org,'day'].to_numpy() for org in sorted_orgs]
# donations_by_org = [ df.loc[df['Org']==org,'Amount'].to_numpy() for org in sorted_orgs]
days_by_org = [ df.loc[df['Org']==org,'day'].to_numpy() for org in sorted_orgs]
donations_by_org = [ df.loc[df['Org']==org,'Amount'].to_numpy() for org in sorted_orgs]

#nonLumpOrgNum = 3 #Number of which not to lump into "others category"
#orgs_with_most = sorted_orgs[len(sorted_orgs)-nonLumpOrgNum:] #nonLumpOrgNum largest organizations
#df['LumpedOrg'] = df.apply(lambda row: row['Org'] if row['Org'] in orgs_with_most else 'Others', axis=1) #Lump organizations
#lumped_org_names = np.append(orgs_with_most,'Others')
# days_by_org_lumped = [ df.loc[df['LumpedOrg']==org,'day'].to_numpy() for org in lumped_org_names]
# donations_by_org_lumped = [ df.loc[df['LumpedOrg']==org,'Amount'].to_numpy() for org in lumped_org_names]

### Plotting ###
min_date = min([days[0] for days in days_by_org])-timedelta(days=1)
max_date = max([days[-1] for days in days_by_org])+timedelta(days=1)
tick_years = [y for y in range(min_date.year, max_date.year+1)]
max_total_donation = sum(donations_by_org[-1])
rows = len(sorted_orgs) + 1
#width_ratios = [0.5, 2, 3, 3]
#gs_kw = {'width_ratios': width_ratios, 'wspace':0, 'hspace':0, 'top':1, 'bottom':0, 'left':0, 'right':0}
vert_spacing = 0.0

def get_plot():
    fig = sp.make_subplots(rows=rows, cols=4, 
                           #shared_xaxes='columns', 
                           column_widths=[0.5, 1.0, 1.5, 1.5],
                           vertical_spacing=0.01, 
                           horizontal_spacing=0.01,
                           specs=[[dict(l=0,r=0,t=0,b=0),{},{},{}] for row in range(rows)]
                        )
    
    fig.add_trace(go.Scatter(x=[0.0],y=[0.5], text='Organisasjon', mode='text',textposition='middle right',textfont=dict(size=14)), row=1, col=2)
    fig.update_xaxes(range=[0,1],row=1, col=2) #In order to align text to left
    fig.add_trace(go.Scatter(x=[0.0],y=[0.5], text='Donasjonshistorikk', mode='text',textposition='middle right',textfont=dict(size=14)), row=1, col=3)
    fig.update_traces(hoverinfo="none", hovertemplate=None, row=1, col=3)
    fig.update_xaxes(range=[0,1],row=1, col=3)
    fig.add_trace(go.Scatter(x=[0.0],y=[0.5], text='Totalt [MNOK]', mode='text',textposition='middle right',textfont=dict(size=14)), row=1, col=4)
    fig.update_xaxes(range=[0,1],row=1, col=4) #In order to align text to left
    fig.add_shape(go.layout.Shape(x0=0, x1=1, y0=1-(1/(rows)), y1=1-(1/(rows)), xref='paper', yref='paper', line=dict(width=1.5)))
    
    for i, org in enumerate(sorted_orgs): #All organizations
        row = rows-i

        fig = add_image_trace(fig, org=org, row=row, col=1)
        fig = add_name_trace(fig, org=org, row=row, col=2)
        fig = add_donation_trace(fig, org=org, row=row, col=3)
        fig = add_histogram_trace(fig, org=org, row=row, col=4)

        #fig.add_shape(go.layout.Shape(x0=0, x1=1, y0=1-(j*(1+vert_spacing)/rows), y1=1-(j*(1+vert_spacing)/rows), xref='paper', yref='paper', line=dict(width=0.5)))
        # line = plt.Line2D((0,1),((i+1)/(rows), (i+1)/(rows)), color="grey", linewidth=2.0 if j==1 else 0.5, transform=fig.transFigure)
        # fig.add_artist(line)

    fig.update_layout(
        showlegend = False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="ESKlarheit"
    )
    fig.for_each_xaxis(lambda x: x.update(showticklabels=False, fixedrange=True, showgrid=False, zeroline=False))
    fig.for_each_yaxis(lambda x: x.update(showticklabels=False, fixedrange=True, showgrid=False, zeroline=False))
    fig.update_traces(hoverinfo="none", hovertemplate=None, col=2)
    if tooltip:
        fig.update_traces(hoverinfo="none", hovertemplate=None, col=3)
    fig.update_traces(hoverinfo="none", hovertemplate=None, col=4)
    
    fig.update_xaxes(
        showticklabels=True, 
        ticks='outside' if sparkline else '',
        dtick='M12',
        tickformat = '%Y',
        ticklabelmode="period",
        row=rows, col=3) #Overwrite hide labels for last trace in column 3
    return fig
