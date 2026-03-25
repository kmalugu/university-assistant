"""
Faculty Directory Tool
Returns faculty and department information.
"""
import json
from pathlib import Path
from typing import Optional

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "faculty" / "faculty_directory.json"


def load_faculty_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_faculty_by_department(department: str) -> list:
    """
    Get all faculty members in a department.

    Args:
        department: Department name (partial match supported)

    Returns:
        List of faculty dicts
    """
    data = load_faculty_data()
    dept_lower = department.lower()
    return [
        f for f in data["faculty"]
        if dept_lower in f["department"].lower()
    ]


def get_faculty_by_name(name: str) -> Optional[dict]:
    """Search faculty by name (partial match)."""
    data = load_faculty_data()
    name_lower = name.lower()
    for f in data["faculty"]:
        if name_lower in f["name"].lower():
            return f
    return None


def get_faculty_for_course(course_code: str) -> Optional[dict]:
    """Get faculty assigned to a specific course."""
    data = load_faculty_data()
    code = course_code.upper()
    for f in data["faculty"]:
        if code in f.get("courses", []):
            return f
    return None


def get_department_info(department: str) -> Optional[dict]:
    """Get department-level information including HOD and contact."""
    data = load_faculty_data()
    dept_lower = department.lower()
    for d in data["departments"]:
        if dept_lower in d["name"].lower():
            return d
    return None


def get_all_departments() -> list:
    """Return list of all departments."""
    data = load_faculty_data()
    return data["departments"]


def format_faculty_card(faculty: dict) -> str:
    """Format a faculty member's info into a readable card."""
    courses = ", ".join(faculty.get("courses", [])) or "N/A"
    return (
        f"👤 {faculty['name']} ({faculty['designation']})\n"
        f"  Department: {faculty['department']}\n"
        f"  Email: {faculty['email']}\n"
        f"  Phone: {faculty['phone']}\n"
        f"  Office: {faculty['office']}\n"
        f"  Consultation Hours: {faculty['consultation_hours']}\n"
        f"  Specialization: {faculty.get('specialization', 'N/A')}\n"
        f"  Courses: {courses}"
    )


def format_department_faculty(department: str) -> str:
    """Format all faculty in a department as text."""
    faculty_list = get_faculty_by_department(department)
    dept_info = get_department_info(department)

    if not faculty_list:
        return f"No faculty found for department: {department}"

    lines = [f"🏫 Department of {department}\n{'='*40}"]
    if dept_info:
        lines.append(
            f"HOD: {dept_info['hod']} | Location: {dept_info['location']}\n"
            f"Dept. Phone: {dept_info['phone']} | Email: {dept_info['email']}\n"
        )
    lines.append(f"Faculty Members ({len(faculty_list)}):\n")
    for f in faculty_list:
        lines.append(format_faculty_card(f))
        lines.append("")

    return "\n".join(lines)
