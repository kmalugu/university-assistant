"""
Academic Calendar Tool
Returns deadlines, exam dates, holidays, and registration windows.
"""
import json
from pathlib import Path
from datetime import datetime, date

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "academic_calendar" / "calendar.json"


def load_calendar():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_calendar_info(program: str = None, query_type: str = "all", semester: str = None) -> dict:
    """
    Get academic calendar information.

    Args:
        program: Student program (BTech, MBA, PhD, MSc)
        query_type: 'deadlines', 'exams', 'holidays', 'registration', 'events', 'all'
        semester: 'odd' or 'even' (default: upcoming)

    Returns:
        dict with requested calendar information
    """
    cal = load_calendar()
    today = date.today()

    # Determine which semester to show
    if semester is None:
        # Auto-pick based on current month
        month = today.month
        semester = "odd" if 7 <= month <= 12 else "even"

    sem_data = cal["semesters"].get(semester, cal["semesters"]["odd"])
    result = {"academic_year": cal["academic_year"], "semester": sem_data["name"]}

    if query_type in ("registration", "all"):
        reg = sem_data["registration_window"]
        result["registration"] = {
            "opens": reg["start"],
            "closes": reg["end"],
            "late_registration_until": reg["late_registration_end"],
            "late_fee": f"Rs. {reg['late_fee']}",
        }

    if query_type in ("holidays", "all"):
        result["holidays"] = sem_data["holidays"]

    if query_type in ("exams", "all"):
        result["internal_exams"] = sem_data["internal_exams"]
        result["end_semester_exams"] = sem_data["end_semester_exams"]
        result["result_declaration"] = sem_data["result_declaration"]

    if query_type in ("events", "all"):
        result["events"] = sem_data.get("events", [])

    if query_type in ("deadlines", "all"):
        result["semester_start"] = sem_data["start"]
        result["semester_end"] = sem_data["end"]
        if program and program in cal.get("program_specific", {}):
            result["program_specific"] = cal["program_specific"][program]

    # Compute upcoming deadlines
    upcoming = []
    for key, label in [
        (sem_data["registration_window"]["end"], "Course Registration Closes"),
        (sem_data["registration_window"]["late_registration_end"], "Late Registration Ends"),
        (sem_data["end_semester_exams"]["start"], "End Semester Exams Begin"),
        (sem_data["result_declaration"], "Results Declared"),
    ]:
        try:
            d = datetime.strptime(key, "%Y-%m-%d").date()
            if d >= today:
                upcoming.append({"date": key, "event": label, "days_left": (d - today).days})
        except Exception:
            pass

    for ia in sem_data.get("internal_exams", []):
        try:
            d = datetime.strptime(ia["start"], "%Y-%m-%d").date()
            if d >= today:
                upcoming.append(
                    {"date": ia["start"], "event": f"{ia['name']} Begins", "days_left": (d - today).days}
                )
        except Exception:
            pass

    upcoming.sort(key=lambda x: x["days_left"])
    result["upcoming_deadlines"] = upcoming[:5]

    return result


def get_next_registration_deadline(program: str = None) -> str:
    """Returns a simple string with the next registration deadline."""
    info = get_calendar_info(program=program, query_type="registration")
    reg = info.get("registration", {})
    closes = reg.get("closes", "N/A")
    late = reg.get("late_registration_until", "N/A")
    return (
        f"Registration for {info.get('semester')} closes on {closes}. "
        f"Late registration (with Rs. 500 fine) is allowed until {late}."
    )
