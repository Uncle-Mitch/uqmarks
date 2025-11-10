import requests
import json
from bs4 import BeautifulSoup
import os
import time
import pandas as pd
from pathlib import Path


THIS_FOLDER = (Path(__file__).parent / "data").resolve()

class CourseMissingError(Exception):
    def __init__(self, course: str):
        self.message = f"The course '{course}' has not been documented yet."
        super().__init__(self.message)

class CourseNotFoundError(Exception):
    def __init__(self, course: str):
        self.message = f"The course '{course}' could not be found or does not exist."
        super().__init__(self.message)

class IncorrectCourseProfileError(Exception):
    def __init__(self, course: str, sem: str, year: str):
        self.message = f"The course profile URL given does not match course '{course}' for Semester {sem} {year}"
        if sem == "3":
            self.message = f"The course profile URL given does not match course '{course}' for Semester {sem} {year}-{year+1}"
        super().__init__(self.message)
        
class WrongSemesterError(Exception):
    def __init__(self, course: str, sem: str):
        self.message = f"The course '{course}' does not exist in the selected semester. (Semester {sem})"
        if sem == "3":
            self.message = f"The course '{course}' does not exist in the summer semester."
        super().__init__(self.message)


def get_table_old(section_code):
    """Get table for courses before 2024 Semester 2

    Args:
        section_code (str): Course code
    """
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )
    url = f'https://www.courses.uq.edu.au/student_section_report.php?report=assessment&profileIds={section_code}'
    page = requests.get(url, headers=headers)

    #Replace with BR to deal with the following:
    # Computer Exercise <br /> Assignment 1
    df_list = pd.read_html(page.text.replace('<br />','||'))
    df = df_list[1] # Gets the asessment table
    df = df.drop(columns=["Course", "Due Date"])

    # Remove jargon like "Computer Exercises" or "Exam during central period.."
    df['Assessment Task'] = df['Assessment Task'].str.partition("||")[2]

    # Edge case where weight = 0% and UQ left the weight 'blank'
    df = df.dropna()
    df['Weighting'] = df['Weighting'].astype(str)
    
    # Edge Case: Identify rows where Weighting does not contain "%" (e.g. DECO2200, DECO7200)
    non_percentage_rows = df.loc[~df['Weighting'].str.contains("%"), 'Weighting']
    
    # If all entries are numeric and equal, convert them to percentages
    if len(non_percentage_rows) > 0 and non_percentage_rows.apply(lambda x: x.isdigit()).all():
        total_tasks = len(non_percentage_rows)
        percentage = 100 / total_tasks
        df.loc[~df['Weighting'].str.contains("%"), 'Weighting'] = f"{percentage:.2f}%"

    # Convert weightings to the appropriate format.
    df.loc[df['Weighting'].str.contains("%"), ['Weighting']] = df['Weighting'].str.partition('%')[0]  + "%"
    # Remove breaklines and extra "change as desired" message
    df.loc[df['Assessment Task'].str.contains("||"), ['Assessment Task']] = df['Assessment Task'].str.partition('||')[0]
    return list(df.itertuples(index=False, name=None))

def get_table(semester, year, course_code, section_code):
    """Gets the assessment items for courses

    Args:
        semester (int): Semester for course
        year (int): year for course
        course_code (str): Course code
        section_code (str): Code for the course profile page
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    # For previous semesters, use old version of course profile
    if (year == 2024 and semester == 1)or year < 2024:
        return get_table_old(section_code)
    
    url = f'https://course-profiles.uq.edu.au/course-profiles/{section_code}#assessment'
    page = requests.get(url, headers=headers)
    html_content = page.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check that course is correct semester and year
    try: 
        hero_section = soup.find('div', class_='hero__text')
        course_info, sem_info = "", ""
        course_info = hero_section.find_all('h1')[0].text.strip()
        sem_info = hero_section.find_all('dd', class_="hero__course-offering__value")[0].text.strip()
        desired_sem = f"Sem {semester} {year}"
        if semester == 3:
            desired_sem = f"Summer {year}"
        if course_code not in course_info or desired_sem not in sem_info:
            raise Exception()
    except:
        raise IncorrectCourseProfileError(course_code, semester, year)

    # Remove <ul class="icon-list"> elements
    for ul in soup.find_all('ul', class_='icon-list'):
        ul.decompose()
    
    # Extract table headings + rows for pandas df
    table = soup.find('table')
    headers = [header.text.strip() for header in table.find_all('th')]
    rows = []
    for row in table.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        rows.append([col.text.strip() for col in cols])
        
    df = pd.DataFrame(rows, columns=headers)
    df = df.drop(columns=["Category", "Due date"])

    # Edge case where weight = 0% and UQ left the weight 'blank'
    df = df.dropna()
    df['Weight'] = df['Weight'].astype(str)
    
    # Edge Case: Identify rows where Weighting does not contain "%" (e.g. DECO2200, DECO7200)
    non_percentage_rows = df.loc[~df['Weight'].str.contains("%"), 'Weight']
    
    # If all entries are numeric and equal, convert them to percentages
    if len(non_percentage_rows) > 0 and non_percentage_rows.apply(lambda x: x.isdigit()).all():
        total_tasks = len(non_percentage_rows)
        percentage = 100 / total_tasks
        df.loc[~df['Weight'].str.contains("%"), 'Weight'] = f"{percentage:.2f}%"

    # Convert weightings to the appropriate format.
    df.loc[df['Weight'].str.contains("%"), ['Weight']] = df['Weight'].str.partition('%')[0]  + "%"
    return list(df.itertuples(index=False, name=None))


def get_assessments(code:str, semester:str, year:str, section_code:str):
    year = int(year)
    semester = int(semester)
    table = get_table(semester, year, code, section_code)

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
    THIS_FOLDER = Path(__file__).parent
    log_dir = THIS_FOLDER / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)  # ensure logs/ exists

    log_path = log_dir / "new_log.txt"
    with log_path.open("a") as file:
        currentTime = int(time.time())
        file.write(f"{currentTime}|{code}|{semester}|{year}\n")

    return table


