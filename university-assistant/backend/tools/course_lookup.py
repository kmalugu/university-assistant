import json
from pathlib import Path
from langchain_core.tools import tool

# Assuming your imports map correctly to where your schemas are saved
from backend.tools.schemas import CourseQuery

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data/course_catalog/courses.json"
FACULTY_FILE = BASE_DIR / "data/faculty/faculty.json"


def load_faculty_map():
    with open(FACULTY_FILE, "r") as f:
        faculty_list = json.load(f)
    return {f["faculty_id"]: f["name"] for f in faculty_list}


@tool(args_schema=CourseQuery)
def get_course_info(course_name: str) -> dict:
    """CRITICAL: You MUST use this tool whenever the user asks for details about a specific course.
    It returns the course ID, credits, department, and assigned faculty.
    DO NOT explain how to call this tool, simply execute it."""

    faculty_map = load_faculty_map()

    try:
        with open(DATA_FILE, "r") as f:
            courses = json.load(f)

        for course in courses:
            if course_name.lower() in course["course_name"].lower():
                return {
                    "course_id": course['course_id'],
                    "course_name": course['course_name'],
                    "credits": course['credits'],
                    "department": course['department'],
                    "faculty": faculty_map.get(course['faculty_id'], "Unknown"),
                }
        return {"error": f"Course matching '{course_name}' not found in the catalog."}

    except FileNotFoundError:
        return {"error": "Course catalog database file not found."}