import json
from pathlib import Path
from langchain_core.tools import tool
from backend.tools.schemas import FeeQuery

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data/fees/fees.json"


@tool(args_schema=FeeQuery)
def get_fee_details(program: str, department: str, year: int) -> dict:
    """CRITICAL: You MUST use this tool whenever the user asks about the cost, tuition, hostel fees, or fee breakdown for a specific program, department, and year.
    DO NOT guess the prices. You must trigger this tool to get the real financial data."""

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        # Helper function to clean strings (removes dots and spaces)
        def clean_text(text: str) -> str:
            return text.replace(".", "").replace(" ", "").lower()

        clean_query_program = clean_text(program)
        clean_query_dept = clean_text(department)

        for item in data:
            if (
                    clean_text(item["program"]) == clean_query_program
                    and clean_text(item["department"]) == clean_query_dept
                    and item["year"] == year
            ):
                return item

        return {"error": f"Fee data not found for Program: {program}, Department: {department}, Year: {year}"}

    except FileNotFoundError:
        return {"error": "Fees database file not found."}
    except Exception as e:
        return {"error": f"An error occurred while fetching fee details: {str(e)}"}