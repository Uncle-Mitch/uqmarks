import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.express as px
from dash import dcc, html
import dash
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

THIS_FOLDER = Path(__file__).parent.resolve()

def load_data(path):
    df = pd.read_csv(path, sep='|', header=None)

    df.columns = ['timestamp', 'code', 'semester', 'year']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df
    

def filter_data(df, semester=None, year=None, start_date=None, end_date=None):
    ## YYYY-MM-DD for start_date and end_date
    if start_date is not None:
        df = df[df['timestamp'] >= start_date]
    
    if end_date is not None:
        df = df[df['timestamp'] <= end_date]

    if semester is not None:
        df = df[df['semester'] == semester]
    
    if year is not None:
        df = df[df['year'] == year]
    
    return df

def search_data(df, code):    
    # Filter DataFrame for the specific code after the start_time
    filtered_data = df[(df['code'] == code)]
    
    return filtered_data

def group_data(df, interval='D'):
    """
    Plot the number of data points over time based on the specified increment.

    Parameters:
    - df (DataFrame): Pandas DataFrame containing a 'timestamp' column as datetime objects.
    - increment (str, optional): The increment to aggregate the data. Defaults to 'D' (day).
      Possible values: 'D' for day, 'W' for week, 'M' for month, 'H' for hour, etc.

    Returns:
    - None: Displays a line graph showing the number of data points over time.
    """
    # Set the 'timestamp' column as the index
    df.set_index('timestamp', inplace=True)

    # Resample the data by the specified increment and count the occurrences
    data_increment = df.resample(interval).size()

    return data_increment

def analyze_frequent_codes(df, top_n=-1, select_code=None):
    # Get the counts of each unique code
    code_counts = df['code'].value_counts().rename_axis('code').reset_index(name='frequency')

    # Select the top N most frequently searched codes
    top_codes = code_counts.head(top_n)
    ranking = None
    if select_code is not None and select_code.upper() in top_codes['code'].values:
        # Zero-based indexing
        ranking = code_counts.loc[code_counts['code'] == select_code.upper()].index[0] + 1 
    
    if select_code and select_code.upper() in code_counts['code'].values \
        and select_code.upper() not in top_codes['code'].values:
        entry = code_counts.loc[code_counts['code'] == select_code.upper()].copy()
        ranking = entry.index[0] + 1 # Zero-based indexing
        entry['code'] = entry['code'] + f" (#{ranking})"
        top_codes = pd.concat([top_codes, entry])
    
    return top_codes, ranking, code_counts

def plot_hourly_usage(df:pd.DataFrame):
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    selected_timezone = 'Australia/Brisbane'

    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(selected_timezone)
    df['hour'] = df['timestamp'].dt.hour # Round datetime to nearest hour

    hourly_grouped = df.groupby(pd.Grouper(key='hour')).size().reset_index(name='count')

    all_hours = pd.DataFrame({'hour': range(24)})
    # Merge with grouped DataFrame to fill missing hours with zero counts
    merged_df = pd.merge(all_hours, hourly_grouped, on='hour', how='left').fillna(0)

    fig = go.Figure(go.Bar(x=merged_df['hour'], y=merged_df['count'], 
                             marker_color='#0D6DCD',
                        )       
                    )
    fig.update_xaxes(title_text='Hour') 
    fig.update_yaxes(title_text='Number Of Searches')

    fig.update_layout(title='Searches For Every Hour',
                  bargap=0)


    fig.update_traces(marker=dict(line=dict(color='black', width=1)))  # Define border color and width
    return fig


def plot_most_frequent_codes(df:pd.DataFrame, highlight_code:str, interval="D"):
    """Returns a plotly bar plot of the most searched codes in the dataframe

    Args:
        df (pd.DataFrame): dataframe of all the searches within a given timeframe
        highlight_code (str): Course Code that user wants to be highlighted
        interval (str, optional): Interval of aggregation (e.g. hourly, daily etc). Defaults to "D".

    Returns:
        px.bar: plotly express bar plot - showing top 10 most searched courses
    """
    fig = go.Figure(data=go.Bar(
        x=df['frequency'],
        y=df['code'],
        orientation='h',
    ))
    
    fig.update_layout(showlegend=False, coloraxis_showscale=False)

    #FF9999
    #48206C
    # :8 for codes outside of top 10 as they have #XX appended to the end.
    fig.update_traces(marker_color=["#FF9999" if highlight_code and code[:8] == highlight_code.upper()
                                    else "#0D6DCD" for code in df['code']])

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': {'title': {'text': 'Number of Searches'}, 'showgrid': True, 'gridcolor':'#C4C4C4'}, 
        'yaxis': {'title': {'text': 'Course Code'}},
        'dragmode': False,
    })

    fig.update_layout(font=dict(family='Arial', size=14, color='black'),
                    margin=dict(l=40, r=20),
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=14,
                        bordercolor='white',
                        font_family='Arial',
                        font=dict(color='black'))
                    )

    # Suppress the default trace name ("trace 0") in hover by adding <extra></extra>.
    fig.update_traces(hovertemplate="<br>".join([
                            "Searches: <b>%{x}</b>",
                            "Course: <b>%{y}</b>",
                            "<extra></extra>"
                        ])
                    ) 

    return fig #, df_code_groups, ranking

def generate_plot(df:pd.DataFrame, code:str, interval="D"):
    """Returns a plotly line graph of all the searches containing a given code.

    Args:
        df (pd.DataFrame): dataframe of all the searches within a given timeframe
        highlight_code (str): Course Code that user wants to be highlighted
        interval (str, optional): Interval of aggregation (e.g. hourly, daily etc). Defaults to "D".

    Returns:
        px.line: plotly express line graph - a graph of date vs searches in every interval
    """
    df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    fig = go.Figure(data=go.Scattergl(
        x=df['timestamp'],
        y=df['frequency'],
        mode='lines',
        name='Search Frequency'
    ))
    fig.update_layout(
        title='Searches Aggregated By Day',
        xaxis_title='Date',
        yaxis_title='Number of Searches',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Do not show "Day" of month
    if interval == "M":
        fig.update_layout({
            'xaxis': {
                'tickformat': '%b %Y'
            }
        })

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': {'title': {'text': 'Date'}, 'showgrid': False, 'zeroline':False}, 
        'yaxis': {'title': {'text': 'Number of Searches'}, 'showgrid': True, 'gridcolor':'#C4C4C4', 'zeroline':False},
        'dragmode': False,
    })

    fig.update_traces(line={'width': 3, 'color':'#48206C'},
                      hovertemplate="<br>".join([
                            "Searches: <b>%{y}</b>"
                        ])
                    )
    fig.update_layout(font=dict(family='Arial', size=14, color='black'),
                     margin=dict(l=40, r=20),
                     hovermode="x unified",
                     hoverlabel=dict(
                        bgcolor="white",
                        font_size=14,
                        bordercolor='white',
                        font_family='Arial'
                    )) 
    
    # Creates vertical spike for x axis
    fig.update_xaxes(showspikes=True, spikecolor="#C4C4C4", spikesnap="cursor", spikemode="across",
                     spikedash="solid", spikethickness=-2)

    return fig, df

def gen_hourly_heatmap(df, code=None):
    """
    """
    grid = pd.MultiIndex.from_product(
        [range(7), range(24)],
        names=['dow', 'hour']
    ).to_frame(index=False)

    # Right/left join doesn’t matter here as long as grid is preserved
    heatmap_data = pd.merge(grid, df, how='left', on=['dow', 'hour'])
    heatmap_data['frequency'] = heatmap_data['frequency'].fillna(0)

    # Map dow → day name and set display order
    dow_to_name = {
        0: 'Sunday',
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday',
    }
    heatmap_data['day_of_week'] = heatmap_data['dow'].map(dow_to_name)

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_order.reverse()  # if you still want Monday at top

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data['frequency'],
        x=heatmap_data['hour'],
        y=heatmap_data['day_of_week'],
        hovertemplate='%{text}<extra></extra>',
        text=heatmap_data.apply(lambda row: f"{row['frequency']} searches on {row['day_of_week']} at {row['hour']}:00", axis=1),
        colorscale='thermal',
        colorbar=dict(title='', tickvals=[heatmap_data['frequency'].min(), heatmap_data['frequency'].max()], ticktext=['Less', 'More']),  # Change colorbar labels
    ))

    # Customize layout
    fig.update_layout(
        title='Searches Throughout The Week',
        xaxis=dict(title='Hour', tickvals=list(range(0, 24, 3))),
        yaxis=dict(title='Day Of Week', categoryorder='array', categoryarray=day_order),
        font=dict(family='Arial', size=14, color='black'),
        margin=dict(l=40, r=20),
        hoverlabel=dict(
            font=dict(family='Arial', color='black'),
            bgcolor="white",
            font_size=14,
            bordercolor='white',
            font_family='Arial'
        )
    )

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
    })


    return fig


def get_modal(page):
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Select Date Range")),
                dbc.ModalBody([
                        dbc.RadioItems(
                            id=f'{page}date-range-radio',
                            options=[
                                {'label': 'Last 30 days', 'value': '30'},
                                {'label': 'Last 3 months', 'value': '90'},
                                {'label': 'Last 6 months', 'value': '180'},
                                {'label': 'Last 12 months', 'value': '365'},
                                {'label': 'All Time', 'value': 'ALL'},
                                {'label': 'Custom', 'value': 'CUSTOM'}
                            ],
                            value='ALL',  # Default value
                            className='radio-items'
                        ),
                        dcc.DatePickerRange(
                            id=f'{page}date-picker-range',
                            display_format='DD/MM/YYYY',
                            min_date_allowed=dt(2023, 2, 1),
                            max_date_allowed=dt.now().date(),
                            initial_visible_month=dt.now(),
                            start_date=dt(2023, 2, 1).date(), # All time hardcoded
                            end_date=dt.now().date(),
                            clearable=False,
                            className="content-font",
                            style={'width': '100%', 'height': '50%', 'border-radius': '6px'}
                            )
                        ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Apply", id=f"{page}close-date", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def get_course_modal(page):
    modal_content = [
            dbc.ModalHeader(dbc.ModalTitle("Filter Course Code")),
            dbc.ModalBody([
                    dbc.Input(
                        id=f"{page}search-input",
                        placeholder="Course Code",
                        className="input analytics-input content-font",
                        type="text",
                        maxLength=8,
                        required=False,
                        autocomplete='off',
                        autofocus=True,
                        style={'width': '100%', 'height': '100%', 'border-radius': '6px', 'border': '1px solid #000', 'padding': '10px', 'color':'#000'}
                        )
                    ]),
            dbc.ModalFooter(
                dbc.Button(
                    "Apply", id=f"{page}close-course", className="ms-auto", n_clicks=0
                )
            ),
        ]
    return modal_content

def get_aggregate_modal(page):
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Aggregate Period:")),
                dbc.ModalBody([
                        dbc.RadioItems(
                            id=f'{page}aggregation-radio',
                            options=[
                                {'label': 'Hourly', 'value': 'H'},
                                {'label': 'Daily', 'value': 'D'},
                                {'label': 'Weekly', 'value': 'W'},
                                {'label': 'Monthly', 'value': 'M'},
                            ],
                            value='D',  # Default value
                            className='radio-items'
                        ),
                        ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Apply", id=f"{page}close-aggregate", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def get_semester_modal(page, semesters_list):
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Choose Semester")),
                dbc.ModalBody([
                        dbc.Select(
                            id=f'{page}semester-select',
                            options=semesters_list,
                            value='NONE',  # Default value
                            className='radio-items'
                        ),
                        html.Br(),
                        dbc.Switch(
                            id=f'{page}semester-switch',
                            label="Automatically change date range to view the chosen semester (e.g. Semester 1: March to July)",
                            value=False,
                        ),
                        dbc.Label("Note: Date range options will be LOCKED if this is selected.")
                        ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Apply", id=f"{page}close-semester", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def gen_home_page():
    return html.Div([
        dash.page_container,           
        ]) 

def get_buttons(page):
    buttons = []
    buttons.append(dbc.Button('Date: All Time', id=f'{page}date-btn', n_clicks=0, 
                              className="content-font", style={'margin-right': '10px',
                                                               "border-radius": '10px', 
                                                               'background-color':'#0D6DCD'}))
    if page != 'hourly-':
        buttons.append(dbc.Button('Course: None', id=f'{page}course-btn', 
                                n_clicks=0, 
                                className="content-font", 
                                style={'margin-right': '10px',"border-radius": '10px', 'background-color':'#0D6DCD'}))
    if page not in ["course-", "hourly-"]:
        buttons.append(dbc.Button('Aggregate: Daily', 
                                  id=f'{page}aggregate-btn',
                                    n_clicks=0, 
                                    className="content-font",
                                      style={'margin-right': '10px',
                                             "border-radius": '10px',
                                               'background-color':'#0D6DCD'
                                               })
        )

    buttons.append(dbc.Button('Semester: None', id=f'{page}semester-btn',
                               n_clicks=0, className="content-font",
                                 style={'margin-right': '10px',"border-radius": '10px',
                                         'background-color':'#0D6DCD'}))
    return buttons



def generate_dashboard(semesters_list, page=""):
    semesters_list["NONE"] = 'None'
    return html.Div([
        html.Div(get_buttons(page), className='date-selector', id='filter-div'),
        dbc.Modal(
            get_modal(page),
            id=f"{page}modal",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_course_modal(page),
            id=f"{page}modal-course",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_aggregate_modal(page),
            id=f"{page}modal-aggregate",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_semester_modal(page, semesters_list),
            id=f"{page}modal-semester",
            is_open=False,
            style={'border':'none'}
        ),
        html.Br(),\
        dbc.Spinner(html.Div(id=f'{page}dynamic-content'), color='#48206C')  
        ], style={'width': '100%', 'height': '100vh', 'margin': '0px', 'padding-left': '40px', 'padding-right': '40px','overflow': 'hidden',
                  'background-color': '#F4EAFF', 'padding-top': '20px'},
        className='justify-align plot-container')

