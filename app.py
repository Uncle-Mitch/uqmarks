import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request
import json
from get_assessment import *
from flask_sqlalchemy import SQLAlchemy
from os import path
from ast import literal_eval as make_tuple
import os
import time
from pathlib import Path


db = SQLAlchemy()
DB_NAME = "course.sqlite"
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
THIS_FOLDER = Path(__file__).parent.resolve()



class Course(db.Model):
    code = db.Column(db.String(8), primary_key=True)
    semester = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    asmts = db.Column(db.String(4000))
db.init_app(app)


def get_course(code:str, semester:str, year:str):
    code=code.upper()
    sem = int(semester)
    yr = int(year)
    found_course = Course.query.filter_by(code=code, year=yr, semester=sem).first()
    if found_course:
        return make_tuple(found_course.asmts)

    weightings = get_assessments(code, semester, year)
    db_asmts = str(weightings)
    new_course = Course(code=code, semester=sem, year=yr, asmts=db_asmts)
    db.session.add(new_course)
    db.session.commit()
    return weightings

def create_database(app):
    if not path.exists(DB_NAME):
        db.create_all(app=app)


@app.route('/', methods=['GET','POST'])
def get_index():
    create_database(app=app)
    return render_template('index.html')

@app.route('/<path:sem>', methods=['GET','POST'])
def redirect_sem_only(sem):
    return redirect('/')

@app.route('/redirect', methods=['GET','POST'])
def redirect_code():
    if request.method == 'POST':
        code = request.form['CourseCode'].upper()
        semester = request.form['Semester']
        return redirect(f'/{semester}/{code}')
    return redirect('/invalid')

@app.route('/invalid', methods=['GET','POST'])
def invalid():
    return render_template('invalid.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )

    data = {
    "content" : "",
    "username" : "UQmarks - QUIZ"
    }

    data["embeds"] = [
        {
            "description" : "Quiz was used",
            "title" : "User opened the quiz page",
        }
    ]
    result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)
    return render_template('quiz.html')

@app.route('/<path:sem>/<path:text>', methods=['GET','POST'])
def all_routes(sem, text):  
    if len(text) == 8 and text[:4].isalpha() and text[4:].isnumeric():
        year, _, semester = sem.partition('S')
        try:
            weightings = get_course(text, semester, year)
        except:
            return render_template('invalid.html', code=text)
        else:
            headers = requests.utils.default_headers()
            headers.update(
                {
                    'User-Agent': 'My User Agent 1.0',
                }
            )

            data = {
            "content" : "",
            "username" : "UQmarks"
            }

            data["embeds"] = [
                {
                    "description" : f"{semester} {year}",
                    "title" : text,
                }
            ]
            
            result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)
            #local logging
            with open(THIS_FOLDER / "logs/search_log.txt","a") as file:
                currentTime = int(time.time())
                file.write(f"{currentTime}|{text}|{semester}|{year}\n")
            return render_template('course_code.html', assessment_list=weightings, code=text, sem=sem)
    else:
        return render_template('invalid.html', code=text)

def start_app():
    create_database(app=app)
    app.run()

if __name__== '__main__':
    start_app()
