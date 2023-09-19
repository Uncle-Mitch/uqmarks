import requests
import json
from bs4 import BeautifulSoup
import os
import time
import pandas as pd
from pathlib import Path


THIS_FOLDER = Path(__file__).parent.resolve()


def return_url(code):
    return f'https://my.uq.edu.au/programs-courses/course.html?course_code={code}'

def get_page(code:str, semester:str , year:str):
    if semester not in ["1", "2"]:
        semester = f"Summer Semester"
    else:
        semester = f'Semester {semester}'
    link = return_url(code)
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )
    page = requests.get(link, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    box = soup.find_all('tr')
    
    if len(box) == 0:
        raise ValueError

    for i in box:
        text = i.text.strip()
        if (year in text and semester in text 
            and ('St Lucia' in text 
                 or 'Herston' in text 
                 or 'Gatton' in text 
                 or 'Ipswich' in text
                 or 'External' in text)
            and 'unavailable' not in text):
            href = i.find_all('a')[2]['href']
            return href


def get_table(section_code):
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )
    url = f'https://www.courses.uq.edu.au/student_section_report.php?report=assessment&profileIds={section_code}'
    page = requests.get(url, headers=headers)

    df_list = pd.read_html(page.text) # Gets all tables in website
    df = df_list[1] # Gets the asessment table
    df = df.drop(columns=["Course", "Due Date"])

    df.loc[df['Weighting'].str.contains("%"), ['Weighting']] = df['Weighting'].str.partition('%')[0]  + "%"
    return list(df.itertuples(index=False, name=None))


def get_assessments(code:str, semester:str, year:str):
    course_profile = get_page(code, semester, year)
    section_code = course_profile.rpartition('/')[2]
    table = get_table(section_code)

    # send to discord
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
            "title" : f"{code} - NEW CODE"
        }
    ]
    
    #local logging of events
    with open(THIS_FOLDER / "logs/new_log.txt","a") as file:
        currentTime = int(time.time())
        file.write(f"{currentTime}|{code}|{semester}|{year}\n")

    result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)
    return table


