"""
Timetable Tool
Returns weekly timetable for a student based on program and year.
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "timetable" / "timetable.json"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def load_timetable():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_timetable(program: str, year: int) -> dict:
    """
    Get the full weekly timetable for a program/year combination.

    Args:
        program: Student program (BTech, MBA, PhD, MSc)
        year: Year of study (1, 2, 3, 4)

    Returns:
        dict keyed by day with list of schedule entries
    """
    data = load_timetable()
    tt = data.get("timetables", {})

    # Normalize program
    program = program.strip()

    program_tt = tt.get(program, {})
    year_key = f"Year{year}"
    year_tt = program_tt.get(year_key, {})

    if not year_tt:
        # Fallback to nearest available
        available = list(program_tt.keys())
        if not available:
            return {"error": f"No timetable found for {program} Year {year}"}
        year_tt = program_tt[available[0]]

    # Add room location details
    locations = data.get("campus_locations", {})
    enriched = {}
    for day, slots in year_tt.items():
        enriched_slots = []
        for slot in slots:
            room = slot.get("room", "")
            loc_info = locations.get(room, {})
            enriched_slots.append({
                **slot,
                "building": loc_info.get("building", ""),
                "floor": loc_info.get("floor", ""),
            })
        enriched[day] = enriched_slots

    return enriched


def get_day_schedule(program: str, year: int, day: str) -> list:
    """Get schedule for a specific day."""
    tt = get_timetable(program, year)
    if "error" in tt:
        return [tt]
    day = day.capitalize()
    return tt.get(day, [])


def get_lab_schedule(program: str, year: int) -> list:
    """Return only lab sessions from the timetable."""
    tt = get_timetable(program, year)
    if "error" in tt:
        return []
    labs = []
    for day, slots in tt.items():
        for slot in slots:
            if slot.get("type") == "Lab":
                labs.append({"day": day, **slot})
    return labs


def format_timetable(program: str, year: int) -> str:
    """Return a formatted text timetable."""
    tt = get_timetable(program, year)
    if "error" in tt:
        return tt["error"]

    lines = [f"📅 Weekly Timetable — {program} Year {year}\n{'='*50}"]
    for day in DAYS:
        slots = tt.get(day, [])
        if not slots:
            lines.append(f"\n{day}: No classes")
            continue
        lines.append(f"\n{day}:")
        for s in slots:
            icon = "🧪" if s["type"] == "Lab" else "📖"
            room_info = f"{s['room']}" + (f" ({s['building']})" if s.get("building") else "")
            lines.append(f"  {icon} {s['time']} | {s['subject']} | {room_info} [{s['type']}]")
    return "\n".join(lines)
