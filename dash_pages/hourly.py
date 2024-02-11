import dash
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from analyse_search import *
import json
from flask_cache import get_semester_list

dash.register_page(__name__, path='/hourly')

layout = generate_dashboard(get_semester_list(), page='hourly-')

