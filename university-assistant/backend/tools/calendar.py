import json
from pathlib import Path
import datetime
from langchain_core.tools import tool
from backend.tools.schemas import DateQuery

DATA_FILE = Path("data/academic_calendar/calendar.json")


@tool(args_schema=DateQuery)
def get_academic_events(date: str):
    """Get academic events for a given date (YYYY-MM-DD)"""

    with open(DATA_FILE, "r") as f:
        events = json.load(f)

    query_date = datetime.datetime.strptime(date, "%Y-%m-%d")

    result = []

    for e in events:
        start = datetime.datetime.strptime(e["start_date"], "%Y-%m-%d")
        end = datetime.datetime.strptime(e["end_date"], "%Y-%m-%d")

        if start <= query_date <= end:
            result.append(e)

    return {
        "date" : date,
        "events" : result if result else "No events found"
    }