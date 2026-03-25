import json
from pathlib import Path

from langchain_core.tools import tool
from backend.tools.schemas import FeeQuery

DATA_FILE = Path("data/fees/fees.json")


@tool(args_schema=FeeQuery)
def get_fee_details(program: str, department: str, year: int):
    """Get fee details"""

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for item in data:
        if (
            item["program"].lower() == program.lower()
            and item["department"].lower() == department.lower()
            and item["year"] == year
        ):
            return item

    return {"error": "Fees data not found"}