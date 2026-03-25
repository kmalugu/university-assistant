from langchain_ollama import ChatOllama

from backend.tools.calendar import get_academic_events
from backend.tools.course_lookup import get_course_info
from backend.tools.faculty import get_faculty
from backend.tools.fees import get_fee_details
from backend.tools.timetable import get_timetable


# Using Llama 3.1 for reliable tool execution
llm = ChatOllama(model='llama3.1', temperature=0)

# Bind tools
tools = [
    get_course_info,
    get_academic_events,
    get_timetable,
    get_fee_details,
    get_faculty
]

llm_with_tools = llm.bind_tools(tools)

def run_tool_agent(query: str, student_profile: dict = None):
    """
    Executes the tool agent with Entity Memory injected into the prompt.
    """
    # Ensure student_profile is at least an empty dictionary if not provided
    if student_profile is None:
        student_profile = {}

    # 1. DYNAMIC SYSTEM PROMPT (ENTITY MEMORY INJECTION)
    # This places the student's exact details directly into the AI's brain for this turn.
    system_prompt = f"""You are a university data routing assistant.

    [ENTITY MEMORY - Current Student Profile]
    - Name: {student_profile.get('name', 'Unknown')}
    - Program: {student_profile.get('program', 'Unknown')}
    - Year: {student_profile.get('year', 'Unknown')}
    - Department: {student_profile.get('department', 'Unknown')}
    - Student ID: {student_profile.get('student_id', 'Unknown')}

    CRITICAL INSTRUCTIONS:
    1. You MUST trigger the appropriate tool to fetch real data when asked about courses, fees, timetables, faculty, or calendar.
    2. If a tool requires arguments (like program, department, year, or student_id) and the user didn't explicitly mention them in their message, YOU MUST EXTRACT THEM FROM THE ENTITY MEMORY above.
    3. Do not explain your thought process. Do not write code blocks. Just call the tool.
    """

    # 2. Pass the dynamic prompt and user query to the LLM
    # We use LangChain's tuple format ("role", "content") for maximum compatibility
    response = llm_with_tools.invoke([
        ("system", system_prompt),
        ("human", query)
    ])

    # 3. Execute the tool if one was called
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        args = tool_call["args"]

        # Map the tool name back to the actual Python function and run it
        tool_map = {t.name: t for t in tools}
        result = tool_map[tool_name].invoke(args)

        return {
            "type": "tool",
            "tool_used": tool_name,
            "result": result
        }

    # 4. Fallback if no tool was called
    return {
        "type": "llm",
        "result": response.content
    }