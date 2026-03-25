import json
from pathlib import Path
from langchain_core.tools import tool
from backend.tools.schemas import StudentQuery

BASE_DIR = Path(__file__).resolve().parents[2]

TIMETABLE_FILE = BASE_DIR / "data/timetable/timetable.json"
STUDENT_FILE = BASE_DIR / "data/students/students.json"


@tool(args_schema=StudentQuery)
def get_timetable(student_id: str) -> dict:
    """CRITICAL: You MUST use this tool whenever a student asks about their classes, schedule, timetable, or where they need to be.
    DO NOT guess the schedule. You must trigger this tool using the student's unique ID to fetch their specific weekly timetable."""

    try:
        # 1. Load student data
        with open(STUDENT_FILE, 'r') as f:
            students = json.load(f)

        student = next((s for s in students if s["student_id"] == student_id), None)

        if not student:
            return {"error": f"Student ID '{student_id}' not found in the database."}

        department = student["department"]
        year = student["year"]

        # Optional: If your students.json has "section", grab it here!
        # section = student.get("section", "A")

        # 2. Load timetable data
        with open(TIMETABLE_FILE, 'r') as f:
            timetable = json.load(f)

        # 3. Filter timetable (Case-insensitive for safety)
        result = [
            t for t in timetable
            if t['department'].lower() == department.lower() and t['year'] == year
        ]

        if not result:
            return {"error": f"Timetable not found for Department: {department}, Year: {year}"}

        return {
            "student_id": student_id,
            "department": department,
            "year": year,
            "timetable": result,
        }

    except FileNotFoundError as e:
        return {"error": f"Database file missing: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred while fetching the timetable: {str(e)}"}