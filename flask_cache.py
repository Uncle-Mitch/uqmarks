from flask_caching import Cache
from datetime import datetime
from pathlib import Path
import json
from analyse_search import load_data

cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300}) 
THIS_FOLDER = Path(__file__).parent.resolve()

def get_semester_list():
    # check if we already cached a recent semester list (within 24 hrs)
    # if already cached, RETURN immediately.
    if cache.get("semester_list") is not None:
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
        if current_month == 12 and latest_year == current_year:
            current_data.insert(0,{'year': current_year, 'semester': 3})
            updated = True
        elif latest_year == (current_year - 1):
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

def get_announcement():
    """
    Returns the announcement from the announcement.json file
    Returns:
        str: Announcement message
    """
    if cache.get("announcement") is not None:
        return cache.get("announcement")
    
    with open(THIS_FOLDER / "announcement.json","r") as f:
        announcement = json.load(f)
        announcement = announcement['current']
    
    # Cache it for 24 hours
    cache.set("announcement", announcement, timeout=60*60*24)
    return announcement

def get_cached_df():
    """
    Dataframe for analytics is updated every 6 hours to reduce overhead in I/O operations
    Returns:
        pd.Dataframe: Current  dataframe of the search activity
    """
    if cache.get("analytics_df") is not None:
        return cache.get("analytics_df")
    
    file_path = THIS_FOLDER / "logs/search_log.txt"
    df = load_data(file_path)

    cache.set("analytics_df", df, timeout=60*60*6) # Cached once every 6 hours
    return df