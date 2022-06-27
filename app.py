import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, request
import json
from get_assessment import *


app = Flask(__name__)

def get_course(code:str, semester:str, year:str):
    weightings = get_assessments('CSSE1001','1', '2022')
    return weightings
    

@app.route('/', methods=['GET','POST'])
def get_index():
    return render_template('index.html')

@app.route('/redirect', methods=['GET','POST'])
def redirect_code():
    if request.method == 'POST':
        code = request.form['CourseCode'].upper()
        return redirect(f'/{code}')
    return redirect('/invalid')

@app.route('/invalid', methods=['GET','POST'])
def invalid():
    return render_template('invalid.html')

@app.route('/<path:text>', methods=['GET','POST'])
def all_routes(text):
    if len(text) == 8 and text[:4].isalpha() and text[4:].isnumeric():
        try:
            weightings = get_assessments(text,'1', '2022')
        except:
            return render_template('invalid.html', code=text)
        else:
            return render_template('course_code.html', assessment_list=weightings, code=text)
    else:
        return render_template('invalid.html', code=text)


if __name__== '__main__':
    app.run()