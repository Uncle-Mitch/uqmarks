import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
import re
from flask import Flask, redirect, request, jsonify, send_from_directory
from flask_cors import cross_origin, CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import json
from get_assessment import *
from log_events import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from os import path
from ast import literal_eval as make_tuple
import os
from pathlib import Path
from flask_caching import Cache
from datetime import datetime
import ipaddress
import socket
from dotenv import load_dotenv
from flask_cache import cache, get_semester_list, get_cached_df, get_announcement, init_cache
from dash_app import create_dash_app
from db_connection import db, Course, SearchLogs, create_database, run_startup_migrations


load_dotenv()

THIS_FOLDER = (Path(__file__).parent / "data").resolve()
DB_NAME = THIS_FOLDER / "course.sqlite"
app = Flask(__name__, static_folder="./react-app/dist", static_url_path="")
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENABLE_LOGGING'] = True if os.environ.get('ENABLE_LOGGING') == "T" else False
CORS(app)
limiter = Limiter(get_remote_address, app=app)
DEBUG_MODE = True if os.environ['DEBUG_MODE'] == "T" else False

cache.init_app(app)

DEFAULT_INVALID_TEXT = "The ECP is currently unavailable or the code is invalid"
    
db.init_app(app)
create_database(app=app)
run_startup_migrations(app=app)
dash_app = create_dash_app(app)

@app.route('/dash', methods=['GET'])
@app.route('/dash/', methods=['GET'])
@app.route('/dash/home', methods=['GET'])
@app.route('/dash/courses', methods=['GET'])
@app.route('/dash/hourly', methods=['GET'])
def redirect_dash():
    """
    Only allow the server to access the dash page instead of everyone
    """
    return dash_app.index()
    if request.referrer is not None and request.referrer.startswith(request.host_url):
        client_ip = request.remote_addr

        # Only allow the server (uqmarks.com) to @access the dash page instead of everyone
        if ipaddress.ip_address(client_ip).is_private:
            return dash_app.index()

    return redirect('/')

@cache.memoize(timeout=86400) # Unlikely for a course weighting to change
def get_course(code:str, semester:str, year:str, section_code:str=None):
    code=code.upper()
    sem = int(semester)
    yr = int(year)
    
    # Check if we have existing db entry for this course
    found_course = db.session.query(Course).filter_by(code=code, year=yr, semester=sem).first()
    if found_course:
        return make_tuple(found_course.asmts)
    
    if section_code is None:
        raise CourseMissingError(code)
    
    weightings = get_assessments(code, semester, year, section_code)
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

def is_valid_course_code(code):
    return bool(re.match(r"^[A-Za-z]{4}[0-9]{4}$", code))

def is_valid_semester_id(semester_id):
    return bool(re.match(r"^\d{4}S[123]$", semester_id))

def course_exists_for_semester_id(course_code, semester_id):
    if not is_valid_course_code(course_code) or not is_valid_semester_id(semester_id):
        return False
    year = int(semester_id.split("S")[0])
    semester = int(semester_id.split("S")[1])
    return db.session.query(Course).filter_by(code=course_code, year=year, semester=semester).first() is not None

def is_valid_course_profile_url(url):
    normal_pattern = bool(re.match(r"^https:\/\/course-profiles\.uq\.edu\.au\/course-profiles\/[A-Za-z]{4}[0-9]{4}-\d+-\d+(#[-A-Za-z0-9]+)?$", url))
    archive_pattern = bool(re.match(r"^https://archive\.course-profiles\.uq\.edu\.au/student_section_loader/section_\d+/\d+$", url))
    return normal_pattern or archive_pattern

@app.errorhandler(RateLimitExceeded)
def handle_ratelimit(e):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please wait before making more requests.'
    }), 429
    

@app.route('/api/semesters/', methods=['GET'])
@cross_origin(origins=["https://www.uqmarks.com", "https://uqmarks.com", "http://localhost:5173", "http://127.0.0.1:5000/"])
@limiter.limit("6/minute")
def api_get_semesters():
    semesters = get_semester_list()
    result = []
    for key in semesters.keys():
        result.append({"value": key, "label": semesters[key]})

    return result


@app.route('/api/getcourse/', methods=['GET'])
@cross_origin(origins=["https://www.uqmarks.com", "https://uqmarks.com", "http://localhost:5173", "http://127.0.0.1:5000/"])
@limiter.limit("100/minute")
def api_get_course():
    course_code = request.args.get('courseCode', '').upper()
    semester_id = request.args.get('semesterId', '')
    course_profile_url = request.args.get('courseProfileUrl', '')

    if not course_code or not semester_id:
        return jsonify({'success': False, 'error': 'Missing course code or semester.'}), 400

    if not is_valid_course_code(course_code) or not is_valid_semester_id(semester_id):
        return jsonify({'success': False, 'error': 'Invalid course code or semester'}), 400
    
    if (len(course_profile_url) > 0 and not is_valid_course_profile_url(course_profile_url)):
        return jsonify({'success': False, 'error': 'Invalid course profile URL', 'showURLRequest': True}), 400
    
    year = semester_id.split("S")[0]
    semester = semester_id.split("S")[1]

    try:
        if len(course_profile_url) > 0:
            match = re.search(
                rf"/course-profiles/({re.escape(course_code)}-\d+-\d+)",
                course_profile_url
            )
            if not match:
                match = re.search(r"/student_section_loader/section_\d+/(\d+)", course_profile_url)
            if not match:
                raise IncorrectCourseProfileError(course_code, semester, year)
            
            section_code = match.group(1)
            weightings = get_course(course_code, semester, year, section_code=section_code)
            assessment_items = []
            for w in weightings:
                assessment_items.append({"title": w[0], "weight": w[1]})
            log_search(course_code, semester, year, THIS_FOLDER, app.config['ENABLE_LOGGING'])

            return jsonify({
                'success': True,
                'courseCode': course_code,
                'semesterId': semester_id,
                'assessmentItems': assessment_items
            })
        else:
            weightings = get_course(course_code, semester, year)
            assessment_items = []
            for w in weightings:
                assessment_items.append({"title": w[0], "weight": w[1]})
            log_search(course_code, semester, year, THIS_FOLDER, app.config['ENABLE_LOGGING'])

            return jsonify({
                'success': True,
                'courseCode': course_code,
                'semesterId': semester_id,
                'assessmentItems': assessment_items
            })
    except CourseMissingError as e:
        return jsonify({'success': False, 'error': '', 'showURLRequest': True}), 404
    except CourseNotFoundError as e:
        return jsonify({'success': False, 'error': str(e.message)}), 400
    except WrongSemesterError as e:
        return jsonify({'success': False, 'error': str(e.message)}), 400
    except IncorrectCourseProfileError as e:
        return jsonify({'success': False, 'error': str(e.message), 'showURLRequest': True}), 400
    except Exception as e:
        log_error(e, course_code, semester, year)
        return jsonify({'success': False, 'error': DEFAULT_INVALID_TEXT}), 400

@app.route('/api/announcement/', methods=['GET'])
@cross_origin(origins=["https://www.uqmarks.com", "https://uqmarks.com", "http://localhost:5173", "http://127.0.0.1:5000/"])
@limiter.limit("3/minute")
def api_get_announcement():

    return jsonify({'success': True, 'announcement': get_announcement()}), 200


@app.route('/api/analytics/page-load/', methods=['POST'])
@cross_origin(origins=["https://www.uqmarks.com", "https://uqmarks.com", "http://localhost:5173", "http://127.0.0.1:5000/"])
@limiter.limit("30/minute")
def api_analytics_page_load():
    max_entries = 25
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return jsonify({'success': False, 'error': 'Invalid JSON payload.'}), 400

    entries = payload.get("entries", [])

    if not isinstance(entries, list):
        return jsonify({'success': False, 'error': 'Invalid entries payload.'}), 400

    if len(entries) > max_entries:
        return jsonify({'success': False, 'error': f'Maximum {max_entries} entries per request.'}), 400

    logged = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        course_code = str(entry.get("courseCode", "")).upper()
        semester_id = str(entry.get("semesterId", ""))

        if not course_exists_for_semester_id(course_code, semester_id):
            continue

        try:
            year, semester = semester_id.split("S", 1)
            log_search(course_code, semester, year, THIS_FOLDER, app.config['ENABLE_LOGGING'], event_type="page_load")
            logged += 1
        except Exception:
            continue

    return jsonify({'success': True, 'logged': logged}), 200

@app.route('/')
@app.route('/course')
@app.route('/analytics')
@app.route('/quiz')
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route('/<path:path>')
def static_proxy(path):
    full_path = os.path.join(app.static_folder, path)
    if os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
    
@app.route("/health")
def health():
    return "ok", 200

def start_app():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=DEBUG_MODE)


if __name__== '__main__':
    start_app()
