import json
from pathlib import Path
from langchain_core.tools import tool
from backend.tools.schemas import DepartmentQuery

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data/faculty/faculty.json"


@tool(args_schema=DepartmentQuery)
def get_faculty(department: str) -> dict:
    """CRITICAL: You MUST use this tool whenever the user asks about professors, faculty, instructors, or staff in a specific department.
    DO NOT guess or make up names. You must trigger this tool to get the real faculty list, emails, and expertise."""

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        result = [
            f for f in data
            if f["department"].lower() == department.lower()
        ]

        if not result:
            return {"error": f"No faculty found for department: {department}"}

        return {
            "department": department,
            "count": len(result),
            "faculty": result
        }

    except FileNotFoundError:
        return {"error": "Faculty database file not found."}