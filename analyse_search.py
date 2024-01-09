import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.express as px
from dash import dcc, html
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dateutil.relativedelta import relativedelta

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
        ranking = code_counts.loc[code_counts['code'] == select_code.upper()].index[0]
    
    if select_code and select_code.upper() in code_counts['code'].values \
        and select_code.upper() not in top_codes['code'].values:
        entry = code_counts.loc[code_counts['code'] == select_code.upper()]
        ranking = entry .index[0]
        top_codes = pd.concat([top_codes, entry])
    
    if ranking is not None:
        ranking += 1 # zero-based indexing
    return top_codes, ranking

def plot_most_frequent_codes(df:pd.DataFrame, highlight_code:str, interval="D"):
    """Returns a plotly bar plot of the most searched codes in the dataframe

    Args:
        df (pd.DataFrame): dataframe of all the searches within a given timeframe
        highlight_code (str): Course Code that user wants to be highlighted
        interval (str, optional): Interval of aggregation (e.g. hourly, daily etc). Defaults to "D".

    Returns:
        px.bar: plotly express bar plot - showing top 10 most searched courses
    """
    df, ranking = analyze_frequent_codes(df, top_n=10, select_code=highlight_code)
    df = df.reset_index()
    del df[df.columns[0]] 

    fig = px.bar(df, x='code', y='frequency', 
                 title='Most Frequently Searched Codes')
    
    fig.update_layout(showlegend=False, coloraxis_showscale=False)

    #FF9999
    #48206C
    index = 0
    colors = ["#8299FF", "#83C135", "#ECA11B", "#2AA170", "#F37EC0", "#F2C428", "#40B3D8", "#8E8CFF", "#EB5DA6", "#39CFC2"]
    markers = []
    for code in fig["data"][0]["x"]:
        if highlight_code and code == highlight_code.upper():
            markers.append("#FF9999")
        else:
            markers.append(colors[index])
            index += 1
    fig["data"][0]["marker"]["color"] = ["#FF9999" if highlight_code and code == highlight_code.upper() 
                                        else "#0D6DCD" for code in fig["data"][0]["x"]]

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',  # Set plot background color
        'paper_bgcolor': 'rgba(0,0,0,0)',  # Set paper background color
        'xaxis': {'title': {'text': 'Course Code'}},  # Customize x-axis
        'yaxis': {'title': {'text': 'Number of Searches'}, 'showgrid': True, 'gridcolor':'#C4C4C4'},  # Customize y-axis
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

    fig.update_traces(hovertemplate="<br>".join([
                            "Course: <b>%{x}</b>",
                            "Searches: <b>%{y}</b>"
                        ])
                    ) 

    return fig, df, ranking

def generate_plot(df:pd.DataFrame, code:str, interval="D"):
    """Returns a plotly line graph of all the searches containing a given code.

    Args:
        df (pd.DataFrame): dataframe of all the searches within a given timeframe
        highlight_code (str): Course Code that user wants to be highlighted
        interval (str, optional): Interval of aggregation (e.g. hourly, daily etc). Defaults to "D".

    Returns:
        px.line: plotly express line graph - a graph of date vs searches in every interval
    """
    if code and len(code) == 8:
        code = code.upper()
        df = search_data(df, code)

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df_daily = group_data(df, interval).to_frame().reset_index()
    df_daily.columns = ['timestamp', 'count']
    df_daily['timestamp'] = pd.to_datetime(df_daily['timestamp'])  # Convert 'timestamp' back to datetime


    fig = px.line(df_daily, x='timestamp', y='count', 
                  title='Searches Aggregated By Day', 
                  labels={'timestamp': 'Date', 'count': 'Number of Searches'})
    
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

def generate_time_range_options():
    return [
        {'label': 'Last 1 month', 'value': '1M'},
        {'label': 'Last 3 months', 'value': '3M'},
        {'label': 'Last 6 months', 'value': '6M'},
        {'label': 'Last 12 months', 'value': '12M'},
        {'label': 'Custom', 'value': 'CUSTOM'}
    ]

def get_modal():
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Select Date Range")),
                dbc.ModalBody([
                        dbc.RadioItems(
                            id='date-range-radio',
                            options=[
                                {'label': 'Last 30 days', 'value': '30'},
                                {'label': 'Last 3 months', 'value': '90'},
                                {'label': 'Last 6 months', 'value': '180'},
                                {'label': 'Last 12 months', 'value': '365'},
                                {'label': 'All Time', 'value': 'ALL'}
                            ],
                            value='ALL',  # Default value
                            className='radio-items'
                        ),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            display_format='DD/MM/YYYY',
                            min_date_allowed=dt(2023, 2, 1),
                            max_date_allowed=(dt.now()-relativedelta(days=1)).date(),
                            initial_visible_month=dt.now(),
                            start_date=(dt.now()-relativedelta(months=6)).date(),
                            clearable=False,
                            className="content-font",
                            style={'width': '100%', 'height': '50%', 'border-radius': '6px'}
                            )
                        ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Apply", id="close-date", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def get_course_modal():
    modal_content = [
            dbc.ModalHeader(dbc.ModalTitle("Filter Course Code")),
            dbc.ModalBody([
                    dbc.Input(
                        id="search-input",
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
                    "Apply", id="close-course", className="ms-auto", n_clicks=0
                )
            ),
        ]
    return modal_content

def get_aggregate_modal():
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Aggregate Period:")),
                dbc.ModalBody([
                        dbc.RadioItems(
                            id='aggregation-radio',
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
                        "Apply", id="close-aggregate", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def get_semester_modal(semesters_list):
    modal_content = [
                dbc.ModalHeader(dbc.ModalTitle("Choose Semester")),
                dbc.ModalBody([
                        dbc.Select(
                            id='semester-select',
                            options=semesters_list,
                            value='NONE',  # Default value
                            className='radio-items'
                        ),
                        html.Br(),
                        dbc.Switch(
                            id='semester-switch',
                            label="Automatically change date range to view the chosen semester (e.g. Semester 1: March to July)",
                            value=False,
                        ),
                        dbc.Label("Note: Date range options will be LOCKED if this is selected.")
                        ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Apply", id="close-semester", className="ms-auto", n_clicks=0
                    )
                ),
            ]
    return modal_content

def generate_dashboard(semesters_list):
    semesters_list["NONE"] = 'None'
    return html.Div([
        html.H3("Filters for the data:"),
        html.Br(),
        html.Div([
            dbc.Button('Date: Last 3 months', id='date-btn', n_clicks=0, className="content-font", style={'margin-right': '10px',"border-radius": '10px', 'background-color':'#0D6DCD'}),
            dbc.Button('Course: None', id='course-btn', n_clicks=0, className="content-font", style={'margin-right': '10px',"border-radius": '10px', 'background-color':'#0D6DCD'}),
            dbc.Button('Aggregate: Daily', id='aggregate-btn', n_clicks=0, className="content-font", style={'margin-right': '10px',"border-radius": '10px', 'background-color':'#0D6DCD'}),
            dbc.Button('Semester: None', id='semester-btn', n_clicks=0, className="content-font", style={'margin-right': '10px',"border-radius": '10px', 'background-color':'#0D6DCD'}),
        ], className='date-selector', id='filter-div'),
        dbc.Modal(
            get_modal(),
            id="modal",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_course_modal(),
            id="modal-course",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_aggregate_modal(),
            id="modal-aggregate",
            is_open=False,
            style={'border':'none'}
        ),
        dbc.Modal(
            get_semester_modal(semesters_list),
            id="modal-semester",
            is_open=False,
            style={'border':'none'}
        ),
        html.Br(),
        html.Div(id='dynamic-content'),        
        ], style={'width': '100%', 'height': '100vh', 'margin': '0px', 'padding': '40px', 'overflow': 'hidden',
                  'background-color': '#F4EAFF'},
        className='justify-align plot-container')