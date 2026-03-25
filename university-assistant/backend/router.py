from backend.agent import run_tool_agent
from backend.rag.rag_chain import rag_chain


def route_query(query: str):
    """
    Decide whether to use:
    - RAG (documents)
    - Tool (structured data)
    """

    query_lower = query.lower()

    # Simple rule-based routing (production can use classifier)
    if any(keyword in query_lower for keyword in [
        "course" , "fees", "timetable", "faculty", "calendar"
    ]):
        return run_tool_agent(query)

    # Default -> RAG
    response = rag_chain.invoke(query)

    return {
        "type" : "rag",
        "result" : response
    }