import json
from pathlib import Path

from langchain_core.tools import tool
from backend.tools.schemas import StudentQuery

TIMETABLE_FILE = Path("data/timetable/timetable.json")
STUDENT_FILE = Path("data/students/students.json")

@tool(args_schema=StudentQuery)
def get_timetable(student_id: str):
    """Get timetable for a student"""

    # Load student data
    with open(STUDENT_FILE, 'r') as f:
        students = json.load(f)

    student = next((s for s in students if s["student_id"] == student_id), None)

    if not student:
        return {"error" : "Student not found"}

    department = student["department"]
    year = student["year"]

    # Load timetable
    with open(TIMETABLE_FILE, 'r') as f:
        timetable = json.load(f)

    # Filter timetable
    result = [
        t for t in timetable
        if t['department'] == department and t['year'] == year
    ]

    if not result:
        return {"error" : "Timetable not found"}

    return {
        "student_id" : student_id,
        "department" : department,
        "year" : year,
        "timetable" : result,
    }