import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request, url_for, jsonify, session
from flask_session import  Session
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
from datetime import datetime, timedelta
import ipaddress
import socket
from dotenv import load_dotenv
from flask_cache import cache, get_semester_list, get_cached_df, get_semester_text, get_announcement
from dash_app import create_dash_app


load_dotenv()
db = SQLAlchemy()
DB_NAME = "course.sqlite"
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENABLE_LOGGING'] = True if os.environ.get('ENABLE_LOGGING') == "T" else False
DEBUG_MODE = True if os.environ['DEBUG_MODE'] == "T" else False
THIS_FOLDER = Path(__file__).parent.resolve()

app.secret_key = os.environ['SECRET_KEY']

cache.init_app(app)

DEFAULT_INVALID_TEXT = "The ECP is currently unavailable or the code is invalid"

class Course(db.Model):
    code = db.Column(db.String(8), primary_key=True)
    semester = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    asmts = db.Column(db.String(4000))

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(15))
    scores = db.Column(db.String(4000))
    session_id = db.Column(db.String(255), nullable=False)
    
db.init_app(app)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_COOKIE_NAME'] = 'UQmarks WAM'

sesh = Session()
sesh.init_app(app)
dash_app = create_dash_app(app)

def is_code_syntax_valid(code: str) -> bool:
    if len(code) == 8 and code[:4].isalpha() and code[4:].isnumeric():
        return True
    return False

@app.route('/dash', methods=['GET'])
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

        # Only allow the server (uqmarks.com) to @access the dash page instead of everyone
        if ipaddress.ip_address(client_ip).is_private:
            return dash_app.index()

    return redirect('/')

@cache.memoize(timeout=86400) # Unlikely for a course weighting to change
def get_course(code:str, semester:str, year:str):
    code=code.upper()
    if not is_code_syntax_valid(code):
        raise CourseNotFoundError(code)
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
    with app.app_context():
        db.create_all()
    if not path.exists(DB_NAME):
        with app.app_context():
            db.create_all()

@app.route('/', methods=['GET','POST'])
def get_index():
    create_database(app=app)
    semesters = get_semester_list()
    return render_template('index.html', 
                           semesters=semesters,
                           announcement=get_announcement())

@app.route('/redirect', methods=['GET','POST'])
def redirect_code():
    if request.method == 'POST':
        code = request.form['CourseCode'].upper()
        semester = request.form['Semester']
        return redirect(f'/{semester}/{code}')
    return redirect('/invalid')

@app.route('/invalid', methods=['GET','POST'])
def invalid():
    return render_template('invalid.html', 
                           semesters=get_semester_list(), 
                           announcement=get_announcement())

@app.route('/quiz', methods=['GET'])
def quiz():
    if app.config['ENABLE_LOGGING']:
        log_quiz()
    return render_template('quiz.html')


## WAM Calculator ##

@app.route('/api/wam/save_score', methods=['POST'])
def wam_save_score():
    course_id = request.form['wam_course_id']
    scores = request.form['scores']
    if not course_id or not scores:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 401

    if not session.get('scores'):
        session['scores'] = {}
    
    session['scores'][course_id] = json.loads(scores)
    
    return jsonify({"message": "Score added successfully"})

@app.route('/api/wam/get_scores', methods=['GET'])
def wam_get_scores():
    if not session.get('scores'):
        session['scores'] = {}
    scores = session['scores']   
    return jsonify({"success": True, "message": "Score retrieved successfully", "scores": scores})

@app.route('/api/wam/add_course', methods=['POST'])
def wam_add_course():
    course_code = request.form['wam_course_code'].upper()
    semester_code = request.form['wam_semester']
    if not course_code or not semester_code:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 401
    
    course_id = f"{course_code}-{semester_code}"
    if course_id in session.get('courses', {}):
        return jsonify({'success': True, 'error': 'Course already exists!'}), 200
    
    semester = semester_code.split("S")[1]
    year = semester_code.split("S")[0]
    try:
        assessment_list = get_course(course_code, semester, year)
    except WrongSemesterError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except CourseNotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'An unexpected error has occurred.'}), 400
    
    display_text = get_semester_text(int(year), int(semester))
    course_info = {"code":course_code, "year": int(year), "semester": int(semester), "assessment_list":assessment_list, "display_text": display_text}
    session['courses'][f"{course_code}-{year}S{semester}"] = course_info

    return jsonify({'success': True, 'message': 'Course added successfully', 'courses': course_info}), 201

@app.route('/api/wam/remove_course', methods=['POST'])
def wam_remove_course():
    course_code = request.form['wam_course_code'].upper()
    semester_code = request.form['wam_semester']
    if not course_code or not semester_code:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    course_id = f"{course_code}-{semester_code}"
    if course_id not in session['courses']:
        return jsonify({'success': True, 'error': 'Course was not in the system'}), 201 

    del session['courses'][f"{course_code}-{semester_code}"]
    del session['scores'][f"{course_code}-{semester_code}"]
    return jsonify({'success': True, 'message': 'Course removed successfully'}), 201

@app.route('/wam', methods=['GET','POST'])
def wam_calculator():  
    # minus sign for descending order
    if not session.get("courses"):
        session["courses"] = {}
    my_courses = session.get('courses', {})
    course_list = list(my_courses.values())
    course_list.sort(key=lambda course: (-course["year"], -course["semester"]))
    return render_template('wam_calculator.html',
                                semesters=get_semester_list(),
                                course_list= course_list,
                                invalid_text="Choose an available semester.",
                                announcement=get_announcement())

@app.route('/<path:sem>/<path:text>', methods=['GET','POST'])
def all_routes(sem, text):
    semesters = get_semester_list()
    if sem not in semesters:
        return render_template('invalid.html', 
                               code=text, 
                               semesters=semesters,
                               sem=sem,
                               invalid_text="Choose an available semester.",
                               announcement=get_announcement())
    
    if is_code_syntax_valid(text):
        year, _, semester = sem.partition('S')
        try:
            weightings = get_course(text, semester, year)
        # We couldn't find the specified course.
        except CourseNotFoundError as e:
            return render_template('invalid.html',
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=e.message,
                                   announcement=get_announcement())
        # Usually happens when the course is not offered in that semester
        except WrongSemesterError as e:
            return render_template('invalid.html',
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=e.message,
                                   announcement=get_announcement())
        except Exception as e:
            if app.config['ENABLE_LOGGING']:
                log_error(e, text, semester, year)
            return render_template('invalid.html', 
                                   code=text,
                                   sem=sem,
                                   semesters=semesters,
                                   invalid_text=DEFAULT_INVALID_TEXT,
                                   announcement=get_announcement())
        else:
            log_search(text, semester, year, THIS_FOLDER, app.config['ENABLE_LOGGING'])
            return render_template('course_code.html', 
                                   assessment_list=weightings, 
                                   code=text, sem=sem, 
                                   semesters=semesters,
                                   announcement=get_announcement())
    else:
        return render_template('invalid.html', 
                               code=text, 
                               semesters=semesters,
                               sem=sem,
                               invalid_text="The code is invalid.",
                               announcement=get_announcement())

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
    app.run(debug=DEBUG_MODE)


if __name__== '__main__':
    start_app()
