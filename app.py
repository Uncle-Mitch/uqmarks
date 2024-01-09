import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, url_for
import json
from get_assessment import *
from analyse_search import *
from log_events import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from os import path
from ast import literal_eval as make_tuple
import os
import time
from pathlib import Path
from flask_caching import Cache
from datetime import datetime
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output, State, ctx
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dateutil.relativedelta import relativedelta
import ipaddress
import socket
from dotenv import load_dotenv
from config import ENABLE_LOGGING, DEBUG_MODE


load_dotenv()
db = SQLAlchemy()
DB_NAME = "course.sqlite"
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
THIS_FOLDER = Path(__file__).parent.resolve()
app.config["CACHE_TYPE"] = "SimpleCache"
cache = Cache(app)

DEFAULT_INVALID_TEXT = "The ECP is currently unavailable or the code is invalid"

class Course(db.Model):
    code = db.Column(db.String(8), primary_key=True)
    semester = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    asmts = db.Column(db.String(4000))
    
db.init_app(app)

@app.route('/dash/', methods=['GET'])
def dash_app():
    if request.referrer is not None and request.referrer.startswith(request.host_url):
        client_ip = request.remote_addr
        hostname = request.url_root.split('://')[1].split(':')[0]  # Extracting the hostname
        host_ip = socket.gethostbyname(hostname)

        # Only allow the server (uqmarks.com) to access the dash page instead of everyone
        if ipaddress.ip_address(client_ip) == ipaddress.ip_address(host_ip):
            return dash_app.index()

    return redirect('/')
    
dash_app = Dash(__name__, server=app, url_base_pathname='/dash/', suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])



def get_course(code:str, semester:str, year:str):
    code=code.upper()
    sem = int(semester)
    yr = int(year)
    
    # Check if we have existing db entry for this course
    found_course_count = db.session.query(Course).filter_by(code=code, year=yr, semester=sem).count()
    if found_course_count >= 1:
        found_course = db.session.query(Course).filter_by(code=code, year=yr, semester=sem).first()
        return make_tuple(found_course.asmts)
    weightings = get_assessments(code, semester, year)
    db_asmts = str(weightings)
    new_course = Course(code=code, semester=sem, year=yr, asmts=db_asmts)
    
    # Sometimes error occurs due to unique constraint, we don't care about
    # it, so we just pass it.
    try:
        db.session.add(new_course)
        db.session.commit()
    except exc.IntegrityError as e:
        pass
    return weightings

def create_database(app):
    if not path.exists(DB_NAME):
        with app.app_context():
            db.create_all()
        

def get_semester_list():
    # check if we already cached a recent semester list (within 24 hrs)
    # if already cached, RETURN immediately.
    if cache.get("semester_list") is not None:
        return cache.get("semester_list")
    
    semesters = {}
    # if there is no cache:
    
    # check if we need to update semesters.json
    current_month = datetime.now().month
    current_year = datetime.now().year
    latest_year = None
    latest_sem = None
    current_data = None
    
    
    #if after march but before july, then semester 1 is the current semester
    with open(THIS_FOLDER / "semesters.json","r") as f:
        current_data = json.load(f)
        latest_sem = current_data[0]["semester"]
        latest_year = current_data[0]["year"]
    
    updated = False
    
    # if current month is between march and july, then semester 1 is the current semester
    if (current_month >= 3) and (current_month < 7) and (latest_sem != 1 or latest_year != current_year):
        current_data.insert(0,{'year': current_year, 'semester': 1})
        updated = True
    
    # if current month is between august and november, then semester 2 is the current semester
    if (current_month >= 8) and (current_month <= 11) and (latest_sem != 2 or latest_year != current_year):
        current_data.insert(0,{'year': current_year, 'semester': 2})
        updated = True
        
    # if current month is between december and february, then semester 3 is the current semester
    if (current_month >= 12) or (current_month <= 2) and latest_sem != 3:
        # should be the year that month 12 is in
        if current_month == 12 and latest_year == current_year:
            current_data.insert(0,{'year': current_year, 'semester': 3})
            updated = True
        elif latest_year == (current_year - 1):
            current_data.insert(0,{'year': current_year-1, 'semester': 3})
            updated = True
        
    # add new data to semesters.json, else read from file
    if updated:
        with open(THIS_FOLDER / "semesters.json","w") as f:
            new_data = json.dumps(current_data)
            f.write(new_data)
    else:
        with open(THIS_FOLDER / "semesters.json","r") as f:
            current_data = json.load(f)
        
    #Load data and format it for the dropdown menu
    for data in current_data:
        year = data["year"]
        sem = data["semester"]
        sem_code = f"{year}S{sem}"
        sem_text = f"Semester {sem} {year}"
        if sem == 3:
            sem_text = f"Summer Semester {year}-{year+1}"
        semesters[sem_code] = sem_text
    
    #cache data for 24 hours
    cache.set("semester_list", semesters, timeout=60*60*24)
    return semesters

def get_cached_df():
    """
    Dataframe for analytics is updated every 6 hours to reduce overhead in I/O operations
    Returns:
        pd.Dataframe: Current  dataframe of the search activity
    """
    if cache.get("analytics_df") is not None:
        return cache.get("analytics_df")
    
    file_path = THIS_FOLDER / "logs/search_log.txt"
    df = load_data(file_path)

    cache.set("analytics_df", df, timeout=60*60*6)
    return df

@app.route('/', methods=['GET','POST'])
def get_index():
    create_database(app=app)
    semesters = get_semester_list()
    return render_template('index.html', semesters=semesters)

@app.route('/redirect', methods=['GET','POST'])
def redirect_code():
    if request.method == 'POST':
        code = request.form['CourseCode'].upper()
        semester = request.form['Semester']
        return redirect(f'/{semester}/{code}')
    return redirect('/invalid')

@app.route('/invalid', methods=['GET','POST'])
def invalid():
    return render_template('invalid.html', semesters=get_semester_list())

@app.route('/quiz', methods=['GET'])
def quiz():
    if app.config['ENABLE_LOGGING']:
        log_quiz()
    return render_template('quiz.html')

@app.route('/<path:sem>/<path:text>', methods=['GET','POST'])
def all_routes(sem, text):
    semesters = get_semester_list()
    if sem not in semesters:
        return render_template('invalid.html', 
                               code=text, 
                               semesters=semesters,
                               sem=sem,
                               invalid_text="Choose an available semester.")
    
    if len(text) == 8 and text[:4].isalpha() and text[4:].isnumeric():
        year, _, semester = sem.partition('S')
        try:
            weightings = get_course(text, semester, year)
        # We couldn't find the specified course.
        except CourseNotFoundError as e:
            return render_template('invalid.html',
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=e.message)
        # Usually happens when the course is not offered in that semester
        except WrongSemesterError as e:
            return render_template('invalid.html',
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=e.message)
        except Exception as e:
            if app.config['ENABLE_LOGGING']:
                log_error(e, text, semester, year)
            return render_template('invalid.html', 
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=DEFAULT_INVALID_TEXT)
        else:
            log_search(text, semester, year, THIS_FOLDER, app.config['ENABLE_LOGGING'])
            return render_template('course_code.html', 
                                   assessment_list=weightings, 
                                   code=text, sem=sem, 
                                   semesters=semesters)
    else:
        return render_template('invalid.html', 
                               code=text, 
                               semesters=semesters,
                               sem=sem,
                               invalid_text="The code is invalid.")

@app.route('/analytics')
def show_analytics():
    return render_template('analytics.html', semesters=get_semester_list())

@dash_app.callback(
    Output('dynamic-content', 'children'),
    Output('date-btn','children'),
    Output('course-btn','children'),
    Output('aggregate-btn','children'),
    Output('semester-btn','children'),
    [
     Input('close-date', 'n_clicks'),
     Input('close-course', 'n_clicks'),
     Input('close-aggregate', 'n_clicks'),
     Input('close-semester', 'n_clicks')
    ],
    [State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date'),
     State('search-input', 'value'),
     State('semester-select', 'value'),
     State('aggregation-radio', 'value'),
     State('semester-switch','value')]
)
def update_output(date_clicks, course_clicks, aggregate_clicks, semester_clicks, start_date, end_date, code, sem_text, interval, sem_lock):
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


    box_style = {
        'padding': '10px',  # Padding inside the box
        'background-color': '#0D6DCD',  # Background color
        'width': '250px',  # Adjust width to fit content
        'margin': '0',
        'color': '#FFFFFF'
    }

    # Define outer box styles with rounded edges
    left_box_style = {
        'background-color': '#4285F4',
        'border-radius': '10px 0 0 10px',  # Rounded corners on the left box
    }

    # Define middle box style without rounded edges
    middle_box_style = {
        'background-color': '#5E35B1',
        'border-radius': '0',  # No rounded corners
    }

    # Define outer box styles with rounded edges
    right_box_style = {
        'background-color': '#00897B',
        'border-radius': '0 10px 10px 0',  # Rounded corners on the right box
    }

    df = get_cached_df()
    df = filter_data(df, year=year, semester=semester, start_date=start_date, end_date=end_date)
    
    fig1, df_code_only = generate_plot(df, code, interval=interval)
    fig2, df_frequency, ranking = plot_most_frequent_codes(df, code, interval=interval)

    # Calculate number of days in timeframe
    if end_date is None:
        analysis_end_date = datetime.now().date()
    else:
        analysis_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    analysis_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    days_elapsed = (analysis_end_date - analysis_start_date).days

    middle_box_text = "Most Searched Course"
    middle_box_value = df_frequency.iloc[0]['code']
    if ranking is not None:
        middle_box_text = f"{code.upper()} ranking"
        middle_box_value = f"#{ranking}"
    
    # Overview statistics
    total_searches = len(df_code_only)
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
        ], style={'display': 'flex'}),  # Display as a row using flexbox
        dcc.Graph(
            id='frequency-chart-1',
            figure=fig1,
            config=config
        ),
        dcc.Graph(
            id='frequency-chart-2',
            figure=fig2,
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
            'Date: Last 3 months',
            f'Course: {code}',
            f'Aggregate: {interval_text[interval]}',
            f'Semester: {semester_list[sem_text]}',
        ]
    
    if sem_lock:
        filter_content[0] = "Date: LOCKED by Semester"
    
    return content, *filter_content

@dash_app.callback(
    Output('date-picker-range', 'start_date'),
    Input('date-range-radio', 'value')
)
def update_date_picker(start_range):
    match start_range:
        case "ALL":
            start_date = dt(2023, 2, 1)
        case "30":
            start_date = dt.now() - relativedelta(days=30)
        case '90':
            start_date = dt.now() - relativedelta(days=90)
        case '180':
            start_date = dt.now() - relativedelta(days=180)
        case '365' | _:
            start_date = dt.now() - relativedelta(days=365)
    # Remove the time portion of datetime object
    start_date = start_date.date()
    return start_date

@dash_app.callback(
    Output("modal", "is_open"),
    [Input("date-btn", "n_clicks"), 
     Input("close-date", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_date_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dash_app.callback(
    Output("modal-course", "is_open"),
    [Input("course-btn", "n_clicks"), 
     Input("close-course", "n_clicks")],
    [State("modal-course", "is_open")],
)
def toggle_course_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dash_app.callback(
    Output("modal-aggregate", "is_open"),
    [Input("aggregate-btn", "n_clicks"), 
     Input("close-aggregate", "n_clicks")],
    [State("modal-aggregate", "is_open")],
)
def toggle_aggregate_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dash_app.callback(
    Output("modal-semester", "is_open"),
    [Input("semester-btn", "n_clicks"), 
     Input("close-semester", "n_clicks")],
    [State("modal-semester", "is_open")],
)
def toggle_semester_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dash_app.callback(
    Output('close-course', 'n_clicks'),
    Input('search-input', 'n_submit')
)
def press_enter_to_click(n_submit):
    return n_submit

@dash_app.callback(
    Output('date-btn', 'disabled'),
    [Input('semester-switch','value'),
    Input('date-range-radio', 'value')]
)
def disable_semester(semester_lock, date_selection):
    if semester_lock:
        return True
    return False

def start_app():
    get_semester_list()
    create_database(app=app)
    app.config['ENABLE_LOGGING'] = ENABLE_LOGGING 
    app.run(debug=DEBUG_MODE)

dash_app.layout = generate_dashboard(get_semester_list())
if __name__== '__main__':
    start_app()
