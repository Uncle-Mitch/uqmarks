import requests
from bs4 import BeautifulSoup
import json
import os
import time
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
    for i in box:
        text = i.text.strip()
        if (year in text and semester in text and ('St Lucia' in text or 'Herston' in text or 'Gatton' in text or 'Ipswich' in text or 'External' in text)
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
    url = f'https://course-profiles.uq.edu.au/student_section_loader/section_5/{section_code}'
    page = requests.get(url, headers=headers)

    soup = BeautifulSoup(page.text, 'html.parser')

    rows = []
    box = soup.find_all('td', class_='text-center')
    row_holder = []
    for child in box:
        em = child.find('em') # don't want embed text
        unwanted = ''

        if em:
            unwanted = em.text
        edited_text = child.text.strip()
        edited_text = edited_text.lstrip(unwanted)
        edited_text = edited_text.replace('  ','')
        edited_text = edited_text.replace('\n','')
        if '%' in edited_text:
            number = edited_text.partition('%')[0] + '%'
        row_holder.append(edited_text)
        if len(row_holder) % 4 == 0:
            start = len(row_holder) - 4
            end = len(row_holder) - 1
            rows.append(row_holder[start:end:2])
    new_rows = []
    for item in rows:
        if not (item[0] == 'Assessment Task' and item[1] == 'Weighting'):
            new_rows.append(item)
    return new_rows


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


