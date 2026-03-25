import json
from pathlib import Path

from langchain_core.tools import tool
from backend.tools.schemas import CourseQuery

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = BASE_DIR / "data/course_catalog/courses.json"

FACULTY_FILE = BASE_DIR / "data/faculty/faculty.json"

def load_faculty_map():
    with open(FACULTY_FILE, "r") as f:
        faculty_list = json.load(f)
    return {f["faculty_id"]: f["name"] for f in faculty_list}

@tool(args_schema=CourseQuery)
def get_course_info(course_name: str):
    """Fetch details of a specific course"""

    faculty_map = load_faculty_map()

    with open(DATA_FILE, "r") as f:
        courses = json.load(f)

    for course in courses:
        if course_name.lower() in course["course_name"].lower():
            return {
                "course_id" : course['course_id'],
                "course_name" : course['course_name'],
                "credits" : course['credits'],
                "department" : course['department'],
                "faculty" : faculty_map.get(course['faculty_id'], "Unknown"),
            }

    return {"error" : "Course not found"}