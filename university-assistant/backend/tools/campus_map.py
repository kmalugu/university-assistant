"""
Campus Map & Navigation Tool
Provides building locations, walking directions, and campus facility info.
"""

# Static campus layout data
CAMPUS_BUILDINGS = {
    "main gate": {
        "description": "Main entrance to the campus (North side, near bus stand)",
        "landmarks": ["Security booth", "Visitor parking", "ATM"],
        "coords": {"lat": 12.9716, "lng": 77.5946},  # Example coordinates
    },
    "admin block": {
        "description": "Central administration building",
        "location": "Center of campus, near auditorium",
        "offices": [
            "Dean of Students (Ground)", "Registrar (Ground)", "Finance Office (1st Floor)",
            "International Student Cell (Room 101)", "Financial Aid (Room 102)",
            "Placement Cell (Ground)", "Dean of Research (3rd Floor, Room 305)"
        ],
        "coords": {"lat": 12.9720, "lng": 77.5950},
    },
    "cs block": {
        "description": "Computer Science department building (East wing)",
        "facilities": ["CS Labs (3 labs)", "Faculty offices", "Seminar room"],
        "coords": {"lat": 12.9718, "lng": 77.5960},
    },
    "ds block": {
        "description": "Data Science department (Adjacent to CS Block, East wing)",
        "facilities": ["DS Labs (2 labs)", "Research area"],
        "coords": {"lat": 12.9717, "lng": 77.5962},
    },
    "math block": {
        "description": "Mathematics department (Near Library)",
        "coords": {"lat": 12.9722, "lng": 77.5948},
    },
    "mba block": {
        "description": "Management department (West wing)",
        "facilities": ["MBA Classrooms", "MBA Lounge", "Case Study Room", "Faculty offices"],
        "coords": {"lat": 12.9718, "lng": 77.5935},
    },
    "lecture hall complex": {
        "description": "Main teaching building in center of campus",
        "facilities": ["LH-101 to LH-401 (20 lecture halls)", "Tutorial rooms"],
        "coords": {"lat": 12.9720, "lng": 77.5945},
    },
    "library": {
        "description": "Central Library — in the heart of campus",
        "hours": "8 AM – 10 PM (Mon-Fri), 9 AM – 6 PM (Sat-Sun)",
        "facilities": ["Print books", "E-resources terminal", "Study rooms", "Reprography"],
        "coords": {"lat": 12.9721, "lng": 77.5944},
    },
    "research block": {
        "description": "Behind the Library",
        "facilities": ["PhD student workspaces", "Research labs", "Seminar rooms"],
        "coords": {"lat": 12.9723, "lng": 77.5943},
    },
    "sports complex": {
        "description": "South campus",
        "facilities": ["Cricket ground", "Football field", "Basketball court", "Swimming pool", "Gymnasium"],
        "hours": "6 AM – 9 PM",
        "coords": {"lat": 12.9705, "lng": 77.5946},
    },
    "cafeteria": {
        "description": "Main Cafeteria is in the Central Block",
        "hours": "7:30 AM – 9:00 PM",
        "variants": {
            "Main Cafeteria": "Central Block — 7:30 AM to 9 PM",
            "Mini Cafeteria (CS Block)": "8 AM to 6 PM",
            "MBA Lounge": "7:30 AM to 8 PM",
        },
        "coords": {"lat": 12.9719, "lng": 77.5947},
    },
    "health center": {
        "description": "University Health Center — near Main Gate",
        "hours": "OPD: 8 AM – 8 PM | Emergency: 24x7",
        "contact": "+91-80-2345-6999",
        "coords": {"lat": 12.9714, "lng": 77.5948},
    },
    "hostel": {
        "description": "Hostel blocks in North and South campus",
        "blocks": {
            "Boys Block A, B, C": "North campus",
            "Girls Block D, E": "South campus",
        },
        "coords": {"lat": 12.9730, "lng": 77.5946},
    },
    "auditorium": {
        "description": "Near Admin Block — capacity 1000",
        "booking": "Contact Student Affairs Office",
        "coords": {"lat": 12.9721, "lng": 77.5950},
    },
    "atm": {
        "description": "ATMs available at 3 locations",
        "locations": ["Near Main Gate", "Near Library", "Hostel Zone"],
    },
}

# Walking directions (simple textual graph)
WALKING_ROUTES = {
    ("main gate", "admin block"): "Walk straight ahead (north) from Main Gate ~200m. Admin Block is the large building on your right.",
    ("main gate", "cs block"): "Enter campus from Main Gate, turn right and walk ~300m along the eastern path. CS Block is the building marked 'CS' on the right.",
    ("main gate", "library"): "Enter campus, walk straight ~350m to the central area. Library is the tall building with glass doors in the center.",
    ("admin block", "library"): "From Admin Block, walk south ~100m. Library is directly behind it.",
    ("admin block", "cs block"): "From Admin Block, take the east corridor ~250m. CS Block is at the end of the path.",
    ("cs block", "ds block"): "DS Block is adjacent to CS Block. Walk ~50m to the south side of CS Block.",
    ("library", "cafeteria"): "Cafeteria is ~100m west of the Library in the Central Block.",
    ("admin block", "sports complex"): "From Admin Block, walk south ~700m through the central path. Sports Complex is on the southern end of campus.",
    ("library", "hostel"): "Boys hostels (A, B, C) are ~400m north of the Library. Girls hostels (D, E) are ~500m south.",
    ("main gate", "health center"): "Health Center is immediately to the left (west) after entering Main Gate, ~80m.",
    ("admin block", "mba block"): "From Admin Block, take the west corridor ~200m. MBA Block is on the left.",
}


def get_building_info(query: str) -> dict:
    """
    Get information about a campus building or facility.

    Args:
        query: Name or partial name of the building/facility

    Returns:
        Building information dict
    """
    query_lower = query.lower()

    # Direct match
    if query_lower in CAMPUS_BUILDINGS:
        return CAMPUS_BUILDINGS[query_lower]

    # Partial match
    for name, info in CAMPUS_BUILDINGS.items():
        if query_lower in name or name in query_lower:
            return {**info, "building_name": name.title()}

    # Keyword search in descriptions
    for name, info in CAMPUS_BUILDINGS.items():
        desc = info.get("description", "").lower()
        offices = " ".join(info.get("offices", [])).lower()
        if query_lower in desc or query_lower in offices:
            return {**info, "building_name": name.title()}

    return {"error": f"Location '{query}' not found on campus map."}


def get_directions(from_location: str, to_location: str) -> str:
    """
    Get walking directions between two campus locations.

    Args:
        from_location: Starting point
        to_location: Destination

    Returns:
        Walking directions string
    """
    from_key = from_location.lower().strip()
    to_key = to_location.lower().strip()

    # Look for direct route
    route = WALKING_ROUTES.get((from_key, to_key)) or WALKING_ROUTES.get((to_key, from_key))
    if route:
        return f"🗺️ Directions from {from_location.title()} to {to_location.title()}:\n{route}"

    # Try via admin block as hub
    via1 = WALKING_ROUTES.get((from_key, "admin block"))
    via2 = WALKING_ROUTES.get(("admin block", to_key))
    if via1 and via2:
        return (
            f"🗺️ Directions (via Admin Block):\n"
            f"Step 1: {via1}\n"
            f"Step 2: {via2}"
        )

    return (
        f"🗺️ Directions from {from_location.title()} to {to_location.title()}:\n"
        f"Head to the Admin Block (center of campus) and ask at the information desk. "
        f"All major buildings are within a 5-10 minute walk from Admin Block.\n"
        f"You can also check the campus map at the main gate or use the university app."
    )


def get_all_facilities() -> str:
    """List all campus facilities."""
    lines = ["🏫 Campus Facilities\n" + "=" * 35]
    for name, info in CAMPUS_BUILDINGS.items():
        desc = info.get("description", "")
        hours = info.get("hours", "")
        line = f"• {name.title()}: {desc}"
        if hours:
            line += f" | Hours: {hours}"
        lines.append(line)
    return "\n".join(lines)
