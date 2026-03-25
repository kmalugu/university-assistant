from backend.agent import run_tool_agent
from backend.rag.rag_chain import rag_chain


def route_query(query: str):
    """
    Decide whether to use:
    - Tool (structured data)
    - RAG (documents)
    """
    query_lower = query.lower()

    # Expanded keyword list for better routing
    tool_keywords = [
        "course", "courses", "prerequisite", "credits",
        "fees", "cost", "tuition", "scholarship",
        "timetable", "schedule", "classes",
        "faculty", "professor", "teacher", "instructor",
        "calendar", "holiday", "exam", "deadline", "event"
    ]

    # Simple rule-based routing
    if any(keyword in query_lower for keyword in tool_keywords):
        return run_tool_agent(query)

    # Default -> RAG (For policies, hostel rules, etc.)
    response = rag_chain.invoke(query)

    return {
        "type" : "rag",
        "result" : response
    }