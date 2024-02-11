import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, url_for
import json
from get_assessment import *
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
import ipaddress
import socket
from dotenv import load_dotenv
from config import ENABLE_LOGGING, DEBUG_MODE
from flask_cache import cache, get_semester_list, get_cached_df
from dash_app import create_dash_app


load_dotenv()
db = SQLAlchemy()
DB_NAME = "course.sqlite"
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
THIS_FOLDER = Path(__file__).parent.resolve()

cache.init_app(app)

DEFAULT_INVALID_TEXT = "The ECP is currently unavailable or the code is invalid"

class Course(db.Model):
    code = db.Column(db.String(8), primary_key=True)
    semester = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    asmts = db.Column(db.String(4000))
    
db.init_app(app)
dash_app = create_dash_app(app)

@app.route('/dash/', methods=['GET'])
@app.route('/dash/home', methods=['GET'])
@app.route('/dash/courses', methods=['GET'])
@app.route('/dash/hourly', methods=['GET'])
def redirect_dash():
    """
    Only allow the server to access the dash page instead of everyone
    """
    if request.referrer is not None and request.referrer.startswith(request.host_url):
        client_ip = request.remote_addr
        hostname = request.url_root.split('://')[1].split(':')[0]  # Extracting the hostname
        host_ip = socket.gethostbyname(hostname)

        # Only allow the server (uqmarks.com) to @access the dash page instead of everyone
        if ipaddress.ip_address(client_ip) == ipaddress.ip_address(host_ip):
            return dash_app.index()

    return redirect('/')

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
@app.route('/analytics/', methods=['GET'])
def show_analytics_home():
    return render_template('analytics.html', page='home', semesters=get_semester_list())

@app.route('/analytics/courses')
def show_analytics_courses():
    return render_template('analytics.html', page='courses', semesters=get_semester_list())

@app.route('/analytics/hourly')
def show_analytics_hourly():
    return render_template('analytics.html', page='hourly', semesters=get_semester_list())


def start_app():
    create_database(app=app)
    app.config['ENABLE_LOGGING'] = os.environ['ENABLE_LOGGING']
    app.run(debug=os.environ['DEBUG_MODE'])


if __name__== '__main__':
    start_app()
