from langchain_ollama import ChatOllama

from backend.tools.calendar import get_academic_events
from backend.tools.course_lookup import get_course_info
from backend.tools.faculty import get_faculty
from backend.tools.fees import get_fee_details
from backend.tools.timetable import get_timetable

# LLM
llm = ChatOllama(model='mistral', temperature=0)


# Bind tools
tools = [
    get_course_info,
    get_academic_events,
    get_timetable,
    get_fee_details,
    get_faculty
]

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """
You are a helpful university assistant. 
You have access to tools for looking up courses, fees, timetables, faculty, and calendars.

CRITICAL INSTRUCTIONS:
- If you need to use a tool to answer the user's question, YOU MUST TRIGGER THE TOOL DIRECTLY.
- DO NOT explain how the tool works. 
- DO NOT output javascript or python code blocks showing how to call the tool.
- Just use the tool.
"""

def run_tool_agent(query: str):
    response = llm_with_tools.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ])

    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        args = tool_call["args"]

        tool_map = {t.name: t for t in tools}
        result = tool_map[tool_name].invoke(args)

        return {
            "type": "tool",
            "tool_used": tool_name,
            "result": result
        }

    return {
        "type": "llm",
        "result": response.content
    }