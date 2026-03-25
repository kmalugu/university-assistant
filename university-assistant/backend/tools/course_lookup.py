"""
Course Lookup Tool
Looks up course details by code or keyword, filtered by program.
"""
import json
from pathlib import Path
from typing import Optional

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "course_catalog" / "courses.json"


def load_courses():
    with open(DATA_PATH, "r") as f:
        return json.load(f)["courses"]


def get_course_by_code(course_code: str) -> Optional[dict]:
    """Fetch a single course by its code (e.g., 'AI101')."""
    courses = load_courses()
    code = course_code.strip().upper()
    for c in courses:
        if c["code"].upper() == code:
            return c
    return None


def search_courses(keyword: str = None, program: str = None, year: int = None, department: str = None) -> list:
    """
    Search courses by keyword, program, year, or department.

    Args:
        keyword: Partial match against title, code, or description
        program: Filter by program (BTech, MBA, MSc, PhD)
        year: Filter by year (1-4)
        department: Filter by department name

    Returns:
        List of matching course dicts
    """
    courses = load_courses()
    results = []

    for c in courses:
        match = True

        if keyword:
            kw = keyword.lower()
            if not (
                kw in c["title"].lower()
                or kw in c["code"].lower()
                or kw in c.get("description", "").lower()
                or any(kw in t.lower() for t in c.get("syllabus", []))
            ):
                match = False

        if program and program not in c.get("programs", []):
            match = False

        if year and c.get("year") != year:
            match = False

        if department and department.lower() not in c.get("department", "").lower():
            match = False

        if match:
            results.append(c)

    return results


def check_prerequisites(course_code: str, completed_courses: list = None) -> dict:
    """
    Check if a student meets prerequisites for a course.

    Args:
        course_code: The course code to check
        completed_courses: List of course codes the student has completed

    Returns:
        dict with 'eligible', 'missing_prerequisites', and 'course' info
    """
    course = get_course_by_code(course_code)
    if not course:
        return {"eligible": False, "error": f"Course {course_code} not found"}

    prereqs = course.get("prerequisites", [])
    if not prereqs:
        return {
            "eligible": True,
            "missing_prerequisites": [],
            "message": f"No prerequisites required for {course_code}",
            "course": course,
        }

    completed = [c.upper() for c in (completed_courses or [])]
    missing = [p for p in prereqs if p.upper() not in completed]

    return {
        "eligible": len(missing) == 0,
        "missing_prerequisites": missing,
        "required_prerequisites": prereqs,
        "message": (
            f"You meet all prerequisites for {course_code}."
            if not missing
            else f"You need to complete: {', '.join(missing)} before taking {course_code}."
        ),
        "course": course,
    }


def format_course_summary(course: dict) -> str:
    """Format a course dict into a human-readable summary."""
    if not course:
        return "Course not found."

    prereqs = ", ".join(course.get("prerequisites", [])) or "None"
    programs = ", ".join(course.get("programs", []))
    syllabus = ", ".join(course.get("syllabus", []))
    lab = f"\n  Lab: {course['lab_timings']}" if course.get("lab_timings") else ""

    return (
        f"📚 {course['code']}: {course['title']}\n"
        f"  Credits: {course['credits']} | Year: {course['year']} | Department: {course['department']}\n"
        f"  Programs: {programs}\n"
        f"  Prerequisites: {prereqs}\n"
        f"  Description: {course.get('description', '')}\n"
        f"  Syllabus: {syllabus}\n"
        f"  Lectures: {course.get('lecture_timings', 'TBA')} — Room {course.get('classroom', 'TBA')}{lab}\n"
        f"  Faculty: {course.get('faculty', 'TBA')}"
    )
