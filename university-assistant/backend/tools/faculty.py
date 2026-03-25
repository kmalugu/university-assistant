import json
from pathlib import Path

from langchain_core.tools import tool
from backend.tools.schemas import DepartmentQuery

DATA_FILE = Path("data/faculty/faculty.json")


@tool(args_schema=DepartmentQuery)
def get_faculty(department: str):
    """Get faculty details for a department"""

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    result = [
        f for f in data
        if f["department"].lower() == department.lower()
    ]

    return {
        "department": department,
        "count": len(result),
        "faculty": result
    }