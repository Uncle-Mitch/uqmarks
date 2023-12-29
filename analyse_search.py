import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.express as px
from dash import dcc, html
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dateutil.relativedelta import relativedelta

THIS_FOLDER = Path(__file__).parent.resolve()

def load_data(path, semester=None, year=None, start_date=None, end_date=None):
    df = pd.read_csv(path, sep='|', header=None)

    df.columns = ['timestamp', 'code', 'semester', 'year']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

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

def group_data(df, increment='D'):
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
    time_words = {'D': 'Day', 'W': 'Week', 'M': 'Month', 'H': 'Hour'}

    # Resample the data by the specified increment and count the occurrences
    data_increment = df.resample(increment).size()

    return data_increment

def analyze_frequent_codes(df, top_n=-1, select_code=None):
    # Get the counts of each unique code
    code_counts = df['code'].value_counts().rename_axis('code').reset_index(name='frequency')

    # Select the top N most frequently searched codes
    top_codes = code_counts.head(top_n)

    if select_code and select_code.upper() in code_counts['code'].values \
        and select_code.upper() not in top_codes['code'].values:
        entry = code_counts.loc[code_counts['code'] == select_code.upper()]
        top_codes = pd.concat([top_codes, entry])
    
    
    return top_codes

def plot_most_frequent_codes(df:pd.DataFrame, highlight_code:str, interval="D"):
    """Returns a plotly bar plot of the most searched codes in the dataframe

    Args:
        df (pd.DataFrame): dataframe of all the searches within a given timeframe
        highlight_code (str): Course Code that user wants to be highlighted
        interval (str, optional): Interval of aggregation (e.g. hourly, daily etc). Defaults to "D".

    Returns:
        px.bar: plotly express bar plot - showing top 10 most searched courses
    """
    df = analyze_frequent_codes(df, top_n=10, select_code=highlight_code).reset_index()
    del df[df.columns[0]] 

    # [(0, "#DBBAFF"), (0.2, "#B368FF"), (0.6, "#682F9E"), (1, "#48206C")]

    fig = px.bar(df, x='code', y='frequency', 
                 title='Most Frequently Searched Codes')
    
    fig.update_layout(showlegend=False, coloraxis_showscale=False)

    fig["data"][0]["marker"]["color"] = ["#FF9999" if highlight_code and code == highlight_code.upper() 
                                         else "#48206C" for code in fig["data"][0]["x"]]

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',  # Set plot background color
        'paper_bgcolor': 'rgba(0,0,0,0)',  # Set paper background color
        'xaxis': {'title': {'text': 'Course Code'}},  # Customize x-axis
        'yaxis': {'title': {'text': 'Number of Searches'}, 'showgrid': True, 'gridcolor':'black'},  # Customize y-axis
        'dragmode': False,
    })

    fig.update_layout(font=dict(family='Arial', size=14, color='black'),
                     margin=dict(l=40, r=20))

    fig.update_traces(hovertemplate="<br>".join([
                            "Course: %{x}",
                            "Searches : %{y}"
                        ])
                    ) 

    return fig, df


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

    # Configure Plotly options
    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': {'title': {'text': 'Date'}, 'showgrid': False}, 
        'yaxis': {'title': {'text': 'Number of Searches'}, 'showgrid': True, 'gridcolor':'black'},
        'dragmode': False,
    })

    fig.update_traces(line={'width': 5, 'color':'#48206C'},
                      hovertemplate="<br>".join([
                            "Date: %{x}",
                            "Searches: %{y}"
                        ])
                    )
    fig.update_layout(font=dict(family='Arial', size=14, color='black'),
                     margin=dict(l=40, r=20)) 

    return fig, df_daily

def generate_time_range_options():
    return [
        {'label': 'Last 1 month', 'value': '1M'},
        {'label': 'Last 3 months', 'value': '3M'},
        {'label': 'Last 6 months', 'value': '6M'},
        {'label': 'Last 12 months', 'value': '12M'},
        {'label': 'Custom', 'value': 'CUSTOM'}
    ]

def generate_dashboard(semesters_list):
    semesters_list["NONE"] = 'None'
    return html.Div([
        html.H3("Filters for the data:"),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    html.Div([
                        dbc.Label("Course Code", className='content-font'),
                        dbc.Input(
                            id="search-input",
                            placeholder="Course Code",
                            className="input analytics-input content-font",
                            type="text",
                            maxLength=8,
                            required=False,
                            autocomplete='off',
                            style={'width': '100%', 'height': '100%', 'border-radius': '6px', 'border': 'none', 'padding': '10px'}
                            ),
                        ]),
                    style={'display': 'inline-block', 'align-items': 'left', 'height': '100%', 'width':'100%'},
                ),
                dbc.Col(
                    html.Div([
                        dbc.Label("Semester", className='content-font'),
                        dbc.Select(
                            id="semester-select",
                            options=semesters_list,
                            value='NONE'
                            )
                    ],
                    className='analytics-input',
                    style={"min-height":'10px', "font-size": "14",
                           "border-radius": '6px'}),
                ),
                dbc.Col(
                    html.Div([
                        dbc.Label("Date Range", className='content-font'),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            display_format='DD/MM/YYYY',
                            min_date_allowed=dt(2023, 2, 1),
                            max_date_allowed=(dt.now()-relativedelta(days=1)).date(),
                            initial_visible_month=dt.now(),
                            start_date=(dt.now()-relativedelta(months=6)).date(),
                            clearable=True,
                            className="content-font",
                            style={'width': '100%', 'height': '50%', 'border-radius': '6px'}
                        )
                    ],
                    style={"width": "100%", "height": "100%", "font-size": "14",
                            "border-radius": '6px','align-items':'center', 
                            'display':'stretch'}),
                ),

            ],
            #justify="evenly",
            style={'margin': '0', "width": "100%", 'height': '4%', 'border-width': '5px', 'align-items': 'left'},
            align='stretch'
        ),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Label("Time Range", className='content-font'),
                    dbc.Select(
                        id='time-range-select',
                        options=generate_time_range_options(),
                        value='12M',  # Default value
                        className="content-font",
                        style={'width': '100%', 'border-radius': '6px'}
                    )
                ]),
                style={'padding-right': '10px'},
                width=6,
            ),
            dbc.Col(
                html.Div([
                    dbc.Label("Aggregate by", className='content-font'),
                    dbc.Select(
                        id='aggregation-select',
                        options=[
                            {'label': 'Hour', 'value': 'H'},
                            {'label': 'Day', 'value': 'D'},
                            {'label': 'Week', 'value': 'W'},
                        ],
                        value='D',  # Default value
                        className="content-font",
                        style={'border-radius': '6px', 'height':'100%'}
                    )
                ]),
                style={'padding-left': '10px', 'height':'100%'},
                width=6,
            ),
        ],
            style={'margin': '40px 0', "width": "66.66%", 'height': '4%', 'border-width': '5px', 'align-items': 'left'},
            align='stretch'
        ), 
        html.Div(id='dynamic-content'),        
        ], style={'width': '100%', 'height': '100vh', 'margin': '0px', 'padding': '40px', 'overflow': 'hidden',
                  'background-color': '#F4EAFF'},
        className='justify-align plot-container')