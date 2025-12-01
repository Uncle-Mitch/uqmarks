from dash import Dash, dcc, html, Input, Output, State, ctx
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from analyse_search import *
from flask_cache import cache, get_semester_list, get_cached_df
from datetime import datetime
import plotly.express as px
from dateutil.relativedelta import relativedelta
import time

from sqlalchemy import create_engine, text, func
from db_connection import get_sqlalchemy_engine, db, SearchLogs, Course
import pandas as pd
import os

def get_search_logs_df():
    """Fetch data from the search_logs table in PostgreSQL and return it as a Pandas DataFrame."""
    query = db.session.query(
        SearchLogs.ts.label("timestamp"),
        SearchLogs.code,
        SearchLogs.semester,
        SearchLogs.year
    )
    with db.engine.connect() as conn:
        return pd.read_sql(query.statement, conn)
    

def group_data_from_db(engine, interval='D'):
    """
    Group data at the database level based on the specified interval.

    Parameters:
    - engine: SQLAlchemy engine connected to the PostgreSQL database.
    - interval (str): The interval for grouping. Defaults to 'D' (day).
      Possible values: 'D' for day, 'W' for week, 'M' for month, 'H' for hour, etc.

    Returns:
    - DataFrame: A Pandas DataFrame containing the grouped data.
    """
    # Map interval to PostgreSQL date_trunc function
    interval_map = {
        'D': 'day',
        'W': 'week',
        'M': 'month',
        'H': 'hour'
    }
    if interval not in interval_map:
        raise ValueError(f"Unsupported interval: {interval}. Use one of {list(interval_map.keys())}.")

    trunc_unit = interval_map[interval]

    query = (
        db.session.query(
            func.date_trunc(trunc_unit, SearchLogs.ts).label("timestamp"),
            func.count().label("frequency")
        )
        .filter(SearchLogs.ts.isnot(None))
        .group_by(func.date_trunc(trunc_unit, SearchLogs.ts))
        .order_by(func.date_trunc(trunc_unit, SearchLogs.ts))
    )
    with db.engine.connect() as conn:
        return pd.read_sql(query.statement, conn)

def get_most_searched_course(engine, limit=1):
    """
    Query the database to find the most searched course.

    Parameters:
    - engine: SQLAlchemy engine connected to the PostgreSQL database.

    Returns:
    - A tuple containing the most searched course code and its frequency.
    """

    query = (
        db.session.query(
            SearchLogs.code.label("code"),
            func.count().label("frequency")
        )
        .group_by(SearchLogs.code)
        .order_by(func.count().desc())
        .limit(limit))

    with db.engine.connect() as conn:
        df = pd.read_sql(query.statement, conn)

    return df

def get_num_unique_courses():
    """Return the number of unique course codes."""
    return db.session.query(db.func.count(db.func.distinct(Course.code))).scalar()

def get_median_searches_per_course():
    """Return the median number of searches per course."""
    subquery = (
        db.session.query(
            SearchLogs.code,
            db.func.count(SearchLogs.id).label("cnt")
        )
        .group_by(SearchLogs.code)
        .subquery()
    )

    median_query = db.session.query(
        db.func.percentile_cont(0.5).within_group(subquery.c.cnt)
    )

    return median_query.scalar()

def get_box_styles() -> tuple[dict]:
    """Returns the style dict for boxes in the analytics page

    Returns:
        tuple[dict]: Style for analytics boxes. [all_boxs, left, middle, right]
    """
    box_style = {
        'padding': '10px',
        'width': '250px',
        'margin': '0',
        'color': '#FFFFFF'
    }

    # Define outer box styles with rounded edges
    left_box_style = {
        'background-color': '#4285F4',
        'border-radius': '10px 0 0 10px',
    }

    # Define middle box style without rounded edges
    middle_box_style = {
        'background-color': '#5E35B1',
        'border-radius': '0', 
    }

    # Define outer box styles with rounded edges
    right_box_style = {
        'background-color': '#00897B',
        'border-radius': '0 10px 10px 0',
    }
    return box_style, left_box_style, middle_box_style, right_box_style

def get_date_str(date_range, start_date, end_date):
    date_time = "None"
    match date_range:
        case "ALL":
            date_time = "All Time"
        case "30":
            date_time = "Last 30 Days"
        case '90':
            date_time = "Last 3 Months"
        case '180':
            date_time = "Last 6 Months"
        case '365':
            date_time = "Last 12 Months"
        case _:
            start_str = datetime.strptime(start_date, '%Y-%m-%d')
            formatted_start = start_str.strftime('%d %b %Y')

            end_str = datetime.strptime(end_date, '%Y-%m-%d')
            formatted_end = end_str.strftime('%d %b %Y')
            date_time = f"{formatted_start} - {formatted_end}"
    return date_time


def get_start_date(start_range:str, current_start_date:str):
    """Returns the start date based on the radio button selected (start_range)

    Args:
        start_range (str): Radio button selected in date range picker
        current_start_date (str): The current start date in format '%Y-%m-%d'

    Returns:
        date: The start date based on the radio button selection.
    """
    match start_range:
        case "ALL":
            start_date = dt(2023, 2, 1)
        case "30":
            start_date = dt.now() - relativedelta(days=30)
        case "90":
            start_date = dt.now() - relativedelta(days=90)
        case "180":
            start_date = dt.now() - relativedelta(days=180)
        case "365":
            start_date = dt.now() - relativedelta(days=365)
        case "CUSTOM" | _:
            return current_start_date
    # Remove the time portion of datetime object
    start_date = start_date.date()
    return start_date

def get_semester_dates(semester:int, year:int):
    start_date, end_date = None, None
    match semester:
        case 1:
            start_date = datetime(year, 3, 1) # 1st March 
            end_date = datetime(year, 7, 10) # 10 July
        case 2:
            start_date = datetime(year, 7, 1) # 1st July 
            end_date = datetime(year, 12, 10) # 10 December
        case 3:
            start_date = datetime(year, 12, 1) # 1st of December
            end_date = datetime(year+1, 2, 28) # 28 Feb


    return start_date.date(), end_date.date()

def get_start_and_end_dates(start_date:str, end_date:str, semester, year, sem_lock, date_range):

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if sem_lock:
        new_start_date, end_date = get_semester_dates(semester, year)
    else:
        new_start_date = get_start_date(date_range, start_date)
    
    new_start_date_str = new_start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    return new_start_date, new_start_date_str, end_date, end_date_str

def create_home_callbacks(dash_app):
    @dash_app.callback(
        [
        Output('home-dynamic-content', 'children'),
        Output('home-date-btn','children'),
        Output('home-course-btn','children'),
        Output('home-aggregate-btn','children'),
        Output('home-semester-btn','children'),
        Output('home-date-picker-range', 'start_date')
        ],
        [
        Input('home-date-range-radio', 'value'),
        Input('home-close-date', 'n_clicks'),
        Input('home-close-course', 'n_clicks'),
        Input('home-aggregation-radio', 'value'),
        Input('home-close-semester', 'n_clicks')
        ],
        [
        State('home-date-picker-range', 'start_date'),
        State('home-date-picker-range', 'end_date'),
        State('home-search-input', 'value'),
        State('home-semester-select', 'value'),
        State('home-aggregation-radio', 'value'),
        State('home-semester-switch','value')],
    )
    def update_output(date_range, date_clicks, course_clicks, aggregate_clicks, semester_clicks, start_date, end_date, code, sem_text, interval, sem_lock):
        start_time = time.time()
        config={
            'displayModeBar': False,
            'displaylogo': False,                                       
            'modeBarButtonsToRemove': ['zoom2d', 'hoverCompareCartesian', 'hoverClosestCartesian', 'toggleSpikelines']
        }
        year, semester = None, None
        if sem_text and sem_text != "NONE":
            year, _, semester = sem_text.partition('S')
            year = int(year)
            semester = int(semester)

        new_start_date, new_start_date_str, end_date, end_date_str = get_start_and_end_dates(start_date, end_date,
                                                                                              semester, year, sem_lock,
                                                                                              date_range)

        engine = get_sqlalchemy_engine()
        grouped_df = group_data_from_db(engine, interval)
        
        # Filter the grouped data based on the selected semester and date range
        grouped_df = grouped_df[
            (grouped_df['timestamp'] >= new_start_date_str) &
            (grouped_df['timestamp'] <= end_date_str)
        ]
        
        fig1, df_code_only = generate_plot(grouped_df.copy(), code, interval=interval)
        most_searched_course, frequency =  get_most_searched_course(engine, 1).iloc[0]

        # Calculate number of days in timeframe
        if end_date is None:
            analysis_end_date = datetime.now().date()
        else:
            analysis_end_date = end_date

        days_elapsed = (analysis_end_date - new_start_date).days

        box_style, left_box_style, middle_box_style, right_box_style = get_box_styles()

        middle_box_text = "Most Searched Course"
        middle_box_value = most_searched_course #df_frequency.loc[df_frequency['frequency'].idxmax(), 'code']
        # if ranking is not None:
        #     middle_box_text = f"{code.upper()} ranking"
        #     middle_box_value = f"#{ranking}"
        
        # Overview statistics
        total_searches = grouped_df['frequency'].sum()
        average_per_day = total_searches / days_elapsed
    
        content = html.Div([
            html.Div([
                # Total Number of Searches
                html.Div([
                    html.P(f"Total Searches", style={'margin': '0'}),
                    html.H3(f"{total_searches}", style={'margin': '0'})],
                    style={**box_style, **left_box_style}
                ),
                # Top Search Query
                html.Div([
                    html.P(f"{middle_box_text}", style={'margin': '0'}),
                    html.H3(f"{middle_box_value}", style={'margin': '0'})],
                    style={**box_style, **middle_box_style}
                ),
                # Average Per Day
                html.Div([
                    html.P(f"Average Per Day", style={'margin': '0'}),
                    html.H3(f"{average_per_day:.2f}", style={'margin': '0'})],
                    style={**box_style, **right_box_style}
                )
            ], style={'display': 'flex'}),
            dcc.Graph(
                id='frequency-chart-1',
                figure=fig1,
                config=config
            )
        ])

        interval_text = {"D":"Daily", "H":"Hourly", "W":"Weekly", "M":"Monthly"}
        semester_list = get_semester_list()
        semester_list["NONE"] = "None"
        if code is None or len(code) == 0:
            code = "None"

        # Updated labels for filter buttons
        filter_content = [
                f'Date: {get_date_str(date_range, new_start_date_str, end_date_str)}',
                f'Course: {code}',
                f'Aggregate: {interval_text[interval]}',
                f'Semester: {semester_list[sem_text]}',
            ]
        
        if sem_lock:
            filter_content[0] = "Date: LOCKED by Semester"
        end_time = time.time()
        print(f"Home callback execution time: {end_time - start_time} seconds")
        return content, *filter_content, new_start_date
    
def create_courses_callbacks(dash_app):
    @dash_app.callback(
        [
        Output('course-dynamic-content', 'children'),
        Output('course-date-btn','children'),
        Output('course-course-btn','children'),
        Output('course-semester-btn','children'),
        Output('course-date-picker-range', 'start_date')
        ],
        [
        Input('course-date-range-radio', 'value'),
        Input('course-close-date', 'n_clicks'),
        Input('course-close-course', 'n_clicks'),
        Input('course-close-semester', 'n_clicks')
        ],
        [
        State('course-date-picker-range', 'start_date'),    
        State('course-date-picker-range', 'end_date'),
        State('course-search-input', 'value'),
        State('course-semester-select', 'value'),
        State('course-semester-switch','value')],
    )
    def update_course_output(date_range, date_clicks, course_clicks, semester_clicks, start_date, end_date, code, sem_text, sem_lock):
        config={
            'displayModeBar': False,
            'displaylogo': False,                                       
            'modeBarButtonsToRemove': ['zoom2d', 'hoverCompareCartesian', 'hoverClosestCartesian', 'toggleSpikelines']
        }
        year, semester = None, None
        if sem_text and sem_text != "NONE":
            year, _, semester = sem_text.partition('S')
            year = int(year)
            semester = int(semester)
        
        new_start_date, new_start_date_str, end_date, end_date_str = get_start_and_end_dates(start_date, end_date,
                                                                                              semester, year, sem_lock,
                                                                                              date_range)
        
        engine = get_sqlalchemy_engine()
        df = get_most_searched_course(engine, 10)
        #df = filter_data(df, year=year, semester=semester, start_date=new_start_date_str, end_date=end_date_str)
        
        fig2 = plot_most_frequent_codes(df, code)
        df_frequency, ranking = None, ""

        box_style, left_box_style, middle_box_style, right_box_style = get_box_styles()

        num_courses = get_num_unique_courses()
        median_num_searches = get_median_searches_per_course()
        # total_searches = df.shape[0]
        # Get % of searches from the top 50 courses
        top_10_percent = 1 #df_frequency.iloc[0:50]['frequency'].sum() / total_searches

        content = html.Div([
            html.Div([
                # Total Number of Searches
                html.Div([
                    html.P(f"Unique Courses Searched", style={'margin': '0'}),
                    html.H3(f"{num_courses}", style={'margin': '0'})],
                    style={**box_style, **left_box_style}
                ),
                # Top Search Query
                html.Div([
                    html.P(f"Median Searches Per Course", style={'margin': '0'}),
                    html.H3(f"{median_num_searches}", style={'margin': '0'})],
                    style={**box_style, **middle_box_style}
                ),
                # Average Per Day
                html.Div([
                    html.P(f"Searches for Top 50 Courses", style={'margin': '0'}),
                    html.H3(f"{top_10_percent*100:.2f}%", style={'margin': '0'})],
                    style={**box_style, **right_box_style}
                )
            ], style={'display': 'flex'}),  # Display as a row using flexbox
            dcc.Graph(
                id='course-chart',
                figure=fig2,
                config=config
            )
        ])

        semester_list = get_semester_list()
        semester_list["NONE"] = "None"
        if code is None or len(code) == 0:
            code = "None"

        # Updated labels for filter buttons
        filter_content = [
                f'Date: {get_date_str(date_range, new_start_date_str, end_date_str)}',
                f'Course: {code}',
                f'Semester: {semester_list[sem_text]}',
            ]
        
        if sem_lock:
            filter_content[0] = "Date: LOCKED by Semester"
        
        return content, *filter_content, new_start_date
    
def create_hourly_callbacks(dash_app):
    @dash_app.callback(
        [
        Output('hourly-dynamic-content', 'children'),
        Output('hourly-date-btn','children'),
        Output('hourly-semester-btn','children'),
        Output('hourly-date-picker-range', 'start_date')
        ],
        [
        Input('hourly-close-date', 'n_clicks'),
        Input('hourly-close-semester', 'n_clicks'),
        Input('hourly-date-range-radio', 'value'),
        ],
        [
        State('hourly-date-picker-range', 'start_date'),
        State('hourly-date-picker-range', 'end_date'),
        State('hourly-semester-select', 'value'),
        State('hourly-semester-switch','value')],
    )
    def update_hourly_output(date_clicks, semester_clicks, date_range, start_date, end_date, sem_text, sem_lock):
        config={
            'displayModeBar': False,
            'displaylogo': False,                                       
            'modeBarButtonsToRemove': ['zoom2d', 'hoverCompareCartesian', 'hoverClosestCartesian', 'toggleSpikelines']
        }
        year, semester = None, None
        if sem_text and sem_text != "NONE":
            year, _, semester = sem_text.partition('S')
            year = int(year)
            semester = int(semester)

        new_start_date, new_start_date_str, end_date, end_date_str = get_start_and_end_dates(start_date, end_date,
                                                                                              semester, year, sem_lock,
                                                                                              date_range)

        df = get_search_logs_df()
        df = filter_data(df, year=year, semester=semester, start_date=new_start_date_str, end_date=end_date_str)
        
        fig = gen_hourly_heatmap(df.copy())
    
        content = html.Div([
            dcc.Graph(
                id='hourly-chart',
                figure=fig,
                config=config
            )
        ])

        semester_list = get_semester_list()
        semester_list["NONE"] = "None"

        date_time = get_date_str(date_range, new_start_date_str, end_date_str)
        
        filter_content = [
                f'Date: {date_time}',
                f'Semester: {semester_list[sem_text]}',
            ]
        
        if sem_lock:
            filter_content[0] = "Date: LOCKED by Semester"
        
        return content, *filter_content, new_start_date
    
def create_general_callbacks(dash_app, page):
        @dash_app.callback(
            Output(f"{page}modal", "is_open"),
            [Input(f"{page}date-btn", "n_clicks"), 
            Input(f"{page}close-date", "n_clicks")],
            [State(f"{page}modal", "is_open")],
        )
        def toggle_date_modal(n1, n2, is_open):
            if n1 or n2:
                return not is_open
            return is_open
        
        if page != "hourly-":
            @dash_app.callback(
                Output(f"{page}modal-course", "is_open"),
                [Input(f"{page}course-btn", "n_clicks"), 
                Input(f"{page}close-course", "n_clicks")],
                [State(f"{page}modal-course", "is_open")],
            )
            def toggle_course_modal(n1, n2, is_open):
                if n1 or n2:
                    return not is_open
                return is_open

        if page == "home-":
            @dash_app.callback(
                Output(f"{page}modal-aggregate", "is_open"),
                [Input(f"{page}aggregate-btn", "n_clicks"), 
                Input(f"{page}close-aggregate", "n_clicks")],
                [State(f"{page}modal-aggregate", "is_open")],
            )
            def toggle_aggregate_modal(n1, n2, is_open):
                if n1 or n2:
                    return not is_open
                return is_open

        @dash_app.callback(
            Output(f"{page}modal-semester", "is_open"),
            [Input(f"{page}semester-btn", "n_clicks"), 
            Input(f"{page}close-semester", "n_clicks")],
            [State(f"{page}modal-semester", "is_open")],
        )
        def toggle_semester_modal(n1, n2, is_open):
            if n1 or n2:
                return not is_open
            return is_open

        @dash_app.callback(
            Output(f'{page}close-course', 'n_clicks'),
            Input(f'{page}search-input', 'n_submit')
        )
        def press_enter_to_click(n_submit):
            return n_submit

        @dash_app.callback(
            Output(f'{page}date-btn', 'disabled'),
            [Input(f'{page}semester-switch','value'),
            Input(f'{page}date-range-radio', 'value')]
        )
        def disable_semester(semester_lock, date_selection):
            if semester_lock:
                return True
            return False
         

def create_dash_app(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/dash/', suppress_callback_exceptions=False,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    use_pages=True,
                    pages_folder="dash_pages",
                    prevent_initial_callbacks="initial_duplicate",
                    meta_tags=[
                        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                    ])

    create_home_callbacks(dash_app)
    create_courses_callbacks(dash_app)
    create_hourly_callbacks(dash_app)

    create_general_callbacks(dash_app, "home-")
    create_general_callbacks(dash_app, "course-")
    create_general_callbacks(dash_app, "hourly-")
    dash_app.layout = gen_home_page() #generate_dashboard(get_semester_list())
    return dash_app