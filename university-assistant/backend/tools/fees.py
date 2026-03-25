"""
Fee Structure & Scholarships Tool
Returns fee breakdown and scholarship information.
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "fees" / "fee_structure.json"


def load_fees():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_fee_breakdown(program: str, nationality: str = "domestic", include_hostel: bool = True) -> dict:
    """
    Get detailed fee breakdown for a program.

    Args:
        program: BTech, MBA, MSc, PhD
        nationality: 'domestic' or 'international'
        include_hostel: Whether to include hostel in total

    Returns:
        Fee breakdown dict
    """
    data = load_fees()
    programs = data.get("programs", {})

    program = program.strip()
    nationality = nationality.lower().strip()

    if program not in programs:
        return {"error": f"Program '{program}' not found. Available: {', '.join(programs.keys())}"}

    prog_data = programs[program]
    nat_data = prog_data.get(nationality, prog_data.get("domestic", {}))

    result = {
        "program": program,
        "nationality": nationality,
        "fee_breakdown": nat_data,
        "payment_deadline": prog_data.get("payment_deadline"),
        "late_fine_per_day": f"Rs. {prog_data.get('late_fine_per_day', 0)}/day",
        "payment_modes": data.get("payment_modes", []),
    }

    if include_hostel:
        total_key = "total_per_semester_with_hostel"
    else:
        total_key = "total_per_semester_without_hostel"

    if total_key in nat_data:
        result["total_per_semester"] = f"Rs. {nat_data[total_key]:,}"

    return result


def get_scholarships(program: str = None, nationality: str = None) -> list:
    """
    Get scholarship information filtered by program/nationality.

    Args:
        program: Filter by program
        nationality: 'domestic' or 'international'

    Returns:
        List of matching scholarships
    """
    data = load_fees()
    scholarships = data.get("scholarships", [])

    results = []
    for s in scholarships:
        if program and program not in s.get("programs", []):
            continue
        # International-specific filter
        if nationality == "international" and "international" not in s["name"].lower():
            if s["name"] in ["Merit Scholarship", "Sports Excellence Scholarship"]:
                pass  # Available to all
            # Allow all unless restricted
        results.append(s)

    return results


def check_scholarship_eligibility(program: str, cgpa: float = None, category: str = None,
                                  nationality: str = "domestic") -> list:
    """
    Check which scholarships a student may be eligible for.

    Args:
        program: Student's program
        cgpa: Student's CGPA
        category: 'general', 'sc', 'st', 'obc', etc.
        nationality: 'domestic' or 'international'

    Returns:
        List of potentially eligible scholarships with reasons
    """
    scholarships = get_scholarships(program=program)
    eligible = []

    for s in scholarships:
        reasons = []
        eligible_flag = True

        # Basic program check
        if program not in s.get("programs", []):
            continue

        name = s["name"]

        if name == "Merit Scholarship" and cgpa:
            if cgpa >= 8.5:
                reasons.append(f"CGPA {cgpa} meets the requirement of >=8.5")
            else:
                eligible_flag = False

        elif name == "SC/ST Scholarship":
            if category and category.lower() in ["sc", "st"]:
                reasons.append(f"Category {category.upper()} is eligible")
            else:
                eligible_flag = False

        elif name == "PhD Research Fellowship":
            if program == "PhD":
                reasons.append("PhD program eligible; GATE/NET qualification required")
            else:
                eligible_flag = False

        elif name == "International Exchange Scholarship":
            if cgpa and cgpa >= 7.5:
                reasons.append(f"CGPA {cgpa} meets requirement of >=7.5")
            elif cgpa:
                eligible_flag = False

        else:
            reasons.append("May be eligible — check specific criteria")

        if eligible_flag:
            eligible.append({
                "scholarship": s["name"],
                "benefit": s["benefit"],
                "application_deadline": s["application_deadline"],
                "eligibility_note": "; ".join(reasons),
                "renewal": s["renewal"],
            })

    return eligible


def format_fee_summary(program: str, nationality: str = "domestic") -> str:
    """Return a formatted text summary of fees."""
    info = get_fee_breakdown(program, nationality)
    if "error" in info:
        return info["error"]

    fd = info["fee_breakdown"]
    lines = [
        f"💰 Fee Structure — {program} ({nationality.title()})\n{'='*45}",
        f"  Tuition: Rs. {fd.get('tuition_per_semester', fd.get('tuition_per_year', 'N/A')):,}",
    ]

    for key, label in [
        ("library_fee", "Library Fee"),
        ("lab_fee", "Lab Fee"),
        ("sports_fee", "Sports Fee"),
        ("medical_fee", "Medical Fee"),
        ("student_activity_fee", "Student Activity Fee"),
        ("case_study_material_fee", "Case Study Materials"),
    ]:
        if key in fd:
            lines.append(f"  {label}: Rs. {fd[key]:,}")

    lines.append(f"\n  🏠 Hostel: Rs. {fd.get('hostel_per_semester', 'N/A'):,}")
    lines.append(f"  🍽️  Mess: Rs. {fd.get('mess_per_semester', 'N/A'):,}")
    lines.append(f"\n  📌 Total/Semester (with hostel): {info.get('total_per_semester', 'N/A')}")
    lines.append(f"  ⏰ Payment Deadline: {info['payment_deadline']}")
    lines.append(f"  ⚠️  Late Fine: {info['late_fine_per_day']}")

    if fd.get("note"):
        lines.append(f"  ℹ️  Note: {fd['note']}")

    return "\n".join(lines)
