"""
Student Support Tool
Handles hostel queries, medical center info, library timings, counseling, etc.
"""

SUPPORT_INFO = {
    "hostel": {
        "blocks": {
            "Boys": ["Block A", "Block B", "Block C"],
            "Girls": ["Block D", "Block E"],
        },
        "warden_contact": {
            "Boys": {"name": "Mr. Ramesh Babu", "phone": "+91-80-2345-6800", "email": "warden.boys@university.edu"},
            "Girls": {"name": "Ms. Kavitha Reddy", "phone": "+91-80-2345-6801", "email": "warden.girls@university.edu"},
        },
        "rules_summary": [
            "Curfew: 10 PM weekdays, 11 PM weekends",
            "Visitors allowed in common room 9 AM – 7 PM",
            "No cooking in rooms",
            "Hostel allotment: first-come-first-served (outstation priority)",
            "Mess timings: Breakfast 7–9 AM, Lunch 12–2 PM, Snacks 4–5 PM, Dinner 7–9 PM",
        ],
        "allotment_process": (
            "1. Fill hostel allotment form on student portal.\n"
            "2. Pay hostel fee (Rs. 35,000/semester domestic).\n"
            "3. Room allotment email sent within 5 working days.\n"
            "4. Report to warden's office with ID and fee receipt."
        ),
        "facilities": ["24x7 security", "WiFi", "Laundry", "Common room with TV", "Indoor games"],
    },
    "library": {
        "hours": {
            "Weekdays": "8:00 AM – 10:00 PM",
            "Saturday": "9:00 AM – 6:00 PM",
            "Sunday": "10:00 AM – 4:00 PM",
            "Holidays": "Closed",
        },
        "borrowing_limits": {
            "BTech": 4,
            "MSc": 4,
            "MBA": 5,
            "PhD": 6,
        },
        "loan_period_days": {"regular": 14, "reference": 3},
        "late_fine": "Rs. 2/day per book",
        "contact": "library@university.edu | Ext: 6006",
        "e_resources": "Available via university VPN. Login at: https://elibrary.university.edu",
        "facilities": [
            "1,50,000+ print books",
            "Online journals (Scopus, Web of Science, JSTOR)",
            "E-books (Springer, Elsevier)",
            "Study rooms (bookable online)",
            "Reprography / printing",
        ],
    },
    "medical": {
        "location": "Near Main Gate",
        "opd_hours": "8:00 AM – 8:00 PM (Mon-Sat)",
        "emergency": "24x7",
        "emergency_contact": "+91-80-2345-6999",
        "email": "healthcenter@university.edu",
        "services": [
            "Free OPD consultation for all students",
            "Basic medicines provided free",
            "Ambulance facility",
            "Dental clinic (Tue/Thu afternoons)",
            "Eye check-up (Wed mornings)",
            "Specialist referrals",
        ],
        "health_insurance": "Group insurance policy for all students — details at Health Center",
        "note": "International students: health insurance is mandatory",
    },
    "counseling": {
        "location": "Admin Block, Room 205",
        "hours": "9:00 AM – 5:00 PM (Mon-Fri)",
        "email": "counseling@university.edu",
        "phone_ext": "6600",
        "booking": "Walk-in or email/call to schedule appointment",
        "services": [
            "Individual counseling (academic stress, anxiety, depression)",
            "Group therapy sessions",
            "Peer support program",
            "Career counseling",
            "Relationship/social skills support",
        ],
        "note": "All sessions are strictly confidential",
    },
    "placement": {
        "location": "Admin Block, Ground Floor",
        "email": "placement@university.edu",
        "phone_ext": "6010",
        "hours": "9:30 AM – 5:30 PM (Mon-Fri)",
        "process": [
            "Register on placement portal (by end of 6th sem for BTech, 2nd sem for MBA)",
            "Attend pre-placement training sessions",
            "Get resume approved by placement cell",
            "Apply to eligible company drives",
            "One placement rule: once offer accepted, cannot apply further in round 1",
        ],
        "cgpa_cutoffs": "Most companies: >= 6.0 CGPA. Top companies: >= 7.5 CGPA",
        "backlogs": "Active backlogs = ineligible for placement drives",
    },
    "finance": {
        "location": "Admin Block, Room 102",
        "email": "finance@university.edu",
        "phone_ext": "6005",
        "hours": "9:00 AM – 5:00 PM (Mon-Fri)",
        "services": ["Fee payment", "Receipt generation", "Refund processing", "Scholarship disbursement"],
    },
}


def get_support_info(category: str) -> dict:
    """
    Get support information for a specific category.

    Args:
        category: hostel, library, medical, counseling, placement, finance

    Returns:
        Information dict
    """
    cat = category.lower().strip()

    # Partial matching
    for key, val in SUPPORT_INFO.items():
        if cat in key or key in cat:
            return {"category": key.title(), **val}

    return {
        "error": f"Category '{category}' not found.",
        "available_categories": list(SUPPORT_INFO.keys()),
    }


def get_hostel_allotment_info() -> str:
    info = SUPPORT_INFO["hostel"]
    return (
        "🏠 Hostel Allotment Process:\n"
        + info["allotment_process"]
        + f"\n\nBoys Warden: {info['warden_contact']['Boys']['name']} | {info['warden_contact']['Boys']['phone']}"
        + f"\nGirls Warden: {info['warden_contact']['Girls']['name']} | {info['warden_contact']['Girls']['phone']}"
    )


def get_library_status(day: str = None) -> str:
    hours = SUPPORT_INFO["library"]["hours"]
    if day:
        day_cap = day.capitalize()
        hour = hours.get(day_cap, hours.get("Weekdays", "Check with library"))
        return f"📚 Library hours on {day_cap}: {hour}"
    lines = ["📚 Library Hours:"]
    for d, h in hours.items():
        lines.append(f"  {d}: {h}")
    return "\n".join(lines)


def get_emergency_contacts() -> str:
    return (
        "🚨 Emergency Contacts:\n"
        "  Health Center (Emergency): +91-80-2345-6999 (24x7)\n"
        "  Anti-Ragging Helpline: 1800-180-5522\n"
        "  Campus Security: +91-80-2345-6911\n"
        "  Dean of Students: dean.students@university.edu | Ext: 6000\n"
        "  Counseling Center: counseling@university.edu | Ext: 6600"
    )
