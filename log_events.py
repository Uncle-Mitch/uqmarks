import os
import requests
import time
import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Load PostgreSQL connection details from environment variables
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),  # Default to localhost if not in Docker
    "port": os.getenv("POSTGRES_PORT", 5432),
}

def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(**DB_CONFIG)

def create_search_logs_table():
    """Create the search_logs table if it doesn't already exist."""
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                code TEXT NOT NULL,
                semester INTEGER NOT NULL,
                year INTEGER NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        
def log_search_to_db(code, semester, year):
    """Log a search event to the PostgreSQL database."""
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO search_logs (code, semester, year)
            VALUES (%s, %s, %s)
            """,
            (code, semester, year)
        )
        conn.commit()
    except Exception as e:
        print(f"Error logging search to database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def log_error(exception:Exception, code:str, semester:str, year:str):
    """Log errors that occur to the discord webhook

    Args:
        exception (Exception): Exception that occurred
        code (str): Course code used as input
        semester (str): Semester used as input
        year (str): Year used as input
    """
    headers = get_headers()
    data = get_data()
    data["content"] = f"<@{os.environ['MANAGER_ID']}> An error has occurred!"
    data["embeds"] = [
        {
            "title" : f"Input: {code} | {semester} | {year}",
            "description" : f"{exception}",
        }
    ]
    result = requests.post(os.environ['ERROR_LOG_LINK'], json = data, headers=headers)

def log_search(code:str, semester:str, year:str, folder, enable_logging:bool):
    """Logs a successful search for a course code.

    Args:
        code (str): Course code used as input
        semester (str): Semester used as input
        year (str): Year used as input
        folder (Path): Path to the folder of search_logs.txt
        enable_logging (bool): If true, also sends to discord webhook. If false, only logs event locally
    """
    headers = get_headers()
    data = get_data()

    data["embeds"] = [
        {
            "description" : f"{semester} {year}",
            "title" : code,
        }
    ]
    if enable_logging:
        requests.post(os.environ['LOG_LINK'], json = data, headers=headers)

    #local logging
    log_search_to_db(code, semester, year)
    with open(folder / "logs/search_log.txt","a") as file:
        currentTime = int(time.time())
        file.write(f"{currentTime}|{code}|{semester}|{year}\n")

def log_quiz():
    """Push a log that the quiz page was opened"""
    headers = get_headers()

    data = get_data()
    data["username"] = "UQmarks - QUIZ"

    data["embeds"] = [
        {
            "description" : "Quiz was used",
            "title" : "User opened the quiz page",
        }
    ]
    result = requests.post(os.environ['LOG_LINK'], json = data, headers=headers)

def get_headers():
    """Returns the necessary headers for webhook"""
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': 'My User Agent 1.0',
        }
    )
    return headers
    

def get_data():
    """Returns the appropriate data format for webhook"""
    data = {
            "content" : "",
            "username" : "UQmarks"
            }
    return data