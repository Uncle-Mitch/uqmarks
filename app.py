import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, url_for
import json
from get_assessment import *
from analyse_search import *
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
from dash import Dash, dcc, html
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dateutil.relativedelta import relativedelta
import ipaddress
import socket

db = SQLAlchemy()
DB_NAME = "course.sqlite"
app = Flask(__name__)
app.config['SECRET_KEY'] = '123'#os.environ['SECRET_KEY']
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

        # Check if the client IP is in the allowed IP list
        if ipaddress.ip_address(client_ip) == ipaddress.ip_address(host_ip):
            # Allow access only if the referrer matches and IP is allowed
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
    if cache.get("semester_list"):
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
        if current_month == 12:
            current_data.insert(0,{'year': current_year, 'semester': 3})
        else:
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


@app.route('/', methods=['GET','POST'])
def get_index():
    create_database(app=app)
    semesters = get_semester_list()
    return render_template('index.html', semesters=semesters)

#@app.route('/<path:sem>', methods=['GET','POST'])
#def redirect_sem_only(sem):
#    return redirect('/')

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

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    headers = get_headers()

    data = get_data()
    data["username"] = "UQmarks - QUIZ"

    data["embeds"] = [
        {
            "description" : "Quiz was used",
            "title" : "User opened the quiz page",
        }
    ]
    #result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)
    return render_template('quiz.html')

@app.route('/<path:sem>/<path:text>', methods=['GET','POST'])
def all_routes(sem, text):
    semesters = get_semester_list()
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
            print(e)
            headers = get_headers()
            data = get_data()
            #data["content"] = f"<@{os.environ['MANAGER_ID']}> An error has occurred!"
            data["embeds"] = [
                {
                    "title" : f"Input: {text}",
                    "description" : f"{e}",
                }
            ]
            #result = requests.post(os.environ['ERROR_LOG_LINK'], json = data, headers=headers)
            return render_template('invalid.html', 
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=DEFAULT_INVALID_TEXT)
        else:
            headers = get_headers()
            data = get_data()

            data["embeds"] = [
                {
                    "description" : f"{semester} {year}",
                    "title" : text,
                }
            ]
            
            #result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)
            #local logging
            with open(THIS_FOLDER / "logs/search_log.txt","a") as file:
                currentTime = int(time.time())
                file.write(f"{currentTime}|{text}|{semester}|{year}\n")
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
    dash.dependencies.Output('dynamic-content', 'children'),
    [dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date'),
     dash.dependencies.Input('search-input', 'value'),
     dash.dependencies.Input('semester-select', 'value'),
     dash.dependencies.Input('aggregation-select', 'value')]
)
def update_output(start_date, end_date, code, sem_text, interval):
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
    return html.Div([
        dcc.Graph(
            id='frequency-chart-1',
            figure=generate_plot(start_date, end_date, code, year=year, semester=semester, interval=interval),
            config=config
        ),
        dcc.Graph(
            id='frequency-chart-2',
            figure=plot_most_frequent_codes(start_date, end_date, code, year=year, semester=semester),
            config=config
        )
    ])

@dash_app.callback(
    dash.dependencies.Output('date-picker-range', 'start_date'),
    dash.dependencies.Input('time-range-select', 'value')
)
def update_date_picker(start_range):
    match start_range:
        case "1M":
            start_date = dt.now() - relativedelta(months=1)
        case '3M':
            start_date = dt.now() - relativedelta(months=3)
        case '6M':
            start_date = dt.now() - relativedelta(months=6)
        case '12M':
            start_date = dt.now() - relativedelta(months=12)
        case _:
            start_date = None  # Default to all time

    return start_date



def start_app():
    semesters_list = get_semester_list()
    
    create_database(app=app)
    app.run(debug=True)
    
def get_headers():
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )
    return headers
    

def get_data():
    data = {
            "content" : "",
            "username" : "UQmarks"
            }
    return data

dash_app.layout = generate_dashboard(get_semester_list())
if __name__== '__main__':
    start_app()
