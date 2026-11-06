"""Run the real analytics UI with synthetic, in-memory searches (no database)."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd
from flask import Flask

import dash_app as analytics
import flask_cache


def generate_searches(seed=42, count=40000):
    """Generate repeatable course popularity and evening usage patterns."""
    rng = random.Random(seed)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    courses = ["CSSE1001", "MATH1051", "CSSE2002", "STAT1201", "MATH1052"]
    courses += [f"{prefix}{level}0{number:02}" for prefix in
                ["ECON", "PSYC", "BIOL", "CHEM", "ENGG"]
                for level in [1, 2, 3] for number in range(1, 6)]
    weights = [1 / (i + 1) ** 0.8 for i in range(len(courses))]
    rows = []
    for _ in range(count):
        day = today - timedelta(days=rng.randrange(365))
        hour = rng.choices(range(24), weights=[1] * 8 + [3] * 9 + [7] * 6 + [2])[0]
        timestamp = day + timedelta(hours=hour, minutes=rng.randrange(60))
        if timestamp > datetime.now():
            timestamp -= timedelta(days=1)
        semester = 1 if 3 <= timestamp.month <= 6 else 2 if 7 <= timestamp.month <= 11 else 3
        year = timestamp.year - (timestamp.month <= 2)
        rows.append((timestamp, rng.choices(courses, weights=weights)[0], year, semester))
    return pd.DataFrame(rows, columns=["timestamp", "code", "year", "semester"])


def create_preview_app():
    """Mount production Dash layouts/callbacks, replacing only their data sources."""
    searches = generate_searches()

    def filtered(year=None, semester=None, start_date=None, end_date=None, code=None):
        frame = searches
        for column, value in [("year", year), ("semester", semester), ("code", code)]:
            if value is not None:
                frame = frame[frame[column] == value]
        if start_date is not None:
            frame = frame[frame.timestamp >= pd.Timestamp(start_date)]
        if end_date is not None:
            frame = frame[frame.timestamp < pd.Timestamp(end_date) + pd.Timedelta(days=1)]
        return frame

    def grouped(engine=None, year=None, semester=None, interval="D", start_date=None, end_date=None, code=None):
        frame = filtered(year, semester, start_date, end_date, code)
        frequencies = {"D": "D", "H": "h", "W": "W-MON", "M": "MS"}
        return (frame.set_index("timestamp").resample(frequencies[interval]).size()
                .rename("frequency").reset_index())

    def ranked(engine=None, year=None, semester=None, limit=1, code=None):
        counts = filtered(year, semester).groupby("code").size().sort_values(ascending=False)
        result = counts.head(limit)
        if code in counts.index and code not in result.index:
            result = pd.concat([result, counts.loc[[code]]])
        if result.empty:
            return pd.DataFrame({"code": ["No searches"], "frequency": [0]})
        return result.rename("frequency").rename_axis("code").reset_index()

    def hourly(year=None, semester=None, start_date=None, end_date=None):
        frame = filtered(year, semester, start_date, end_date).copy()
        frame["dow"] = (frame.timestamp.dt.dayofweek + 1) % 7
        frame["hour"] = frame.timestamp.dt.hour
        return frame.groupby(["dow", "hour"]).size().rename("frequency").reset_index()

    def unique(**filters):
        return filtered(**filters).code.nunique()

    def median(**filters):
        counts = filtered(**filters).groupby("code").size()
        return float(counts.median()) if not counts.empty else 0

    def top_share(**filters):
        counts = filtered(**filters).groupby("code").size()
        return counts.nlargest(50).sum() / counts.sum() if not counts.empty else 0

    def semesters():
        pairs = searches[["year", "semester"]].drop_duplicates().sort_values(
            ["year", "semester"], ascending=False
        )
        return {f"{year}S{semester}": f"Semester {semester} {year}"
                for year, semester in pairs.itertuples(index=False, name=None)}

    # Changes exist only in this separate development process; nothing is seeded
    # into a database or enabled in app.py/the production entry point.
    analytics.get_sqlalchemy_engine = lambda: None
    analytics.group_data_from_db = grouped
    analytics.get_most_searched_course = ranked
    analytics.get_search_logs_df = hourly
    analytics.get_num_unique_courses = unique
    analytics.get_median_searches_per_course = median
    analytics.get_searches_for_top_50_courses = top_share
    analytics.get_semester_list = semesters
    flask_cache.get_semester_list = semesters

    server = Flask(__name__, static_folder=str(Path(__file__).parent / "react-app" / "dist"), static_url_path="")
    flask_cache.cache.init_app(server)
    analytics.create_dash_app(server)

    @server.route("/")
    @server.route("/analytics")
    def frontend():
        return server.send_static_file("index.html")

    print(f"Fake analytics ready: {len(searches):,} searches across {searches.code.nunique()} courses.")
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    create_preview_app().run(host="127.0.0.1", port=args.port, debug=False)
