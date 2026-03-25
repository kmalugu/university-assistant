"""
FastAPI Backend — University Student Information & Guidance Assistant
Endpoints: /chat, /course, /timetable, /fees, /calendar, /rag, /faculty
"""
import logging
import sys
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent import get_agent
from backend.rag.retriever import get_retriever
from backend.rag.vector_store import initialize_vector_store
from backend.memory.student_memory import get_memory_manager, clear_session
from backend.cache import get_cache_stats, invalidate_cache
from backend.tools.course_lookup import get_course_by_code, search_courses, check_prerequisites
from backend.tools.timetable import get_timetable, format_timetable, get_lab_schedule
from backend.tools.fees import get_fee_breakdown, get_scholarships, check_scholarship_eligibility, format_fee_summary
from backend.tools.calendar import get_calendar_info, get_next_registration_deadline
from backend.tools.faculty import (
    get_faculty_by_department, get_faculty_by_name,
    format_department_faculty, get_all_departments,
)
from backend.tools.campus_map import get_building_info, get_directions
from backend.tools.student_support import get_support_info, get_emergency_contacts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="University Student Assistant API",
    description="AI-powered campus guidance assistant for students",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Session ID (auto-generated if not provided)")
    message: str = Field(..., description="Student's message")

class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str
    tool_used: str
    sources: List[str]
    student_profile: dict

class CourseRequest(BaseModel):
    course_code: Optional[str] = None
    keyword: Optional[str] = None
    program: Optional[str] = None
    year: Optional[int] = None
    completed_courses: Optional[List[str]] = []

class TimetableRequest(BaseModel):
    program: str
    year: int = 1

class FeesRequest(BaseModel):
    program: str
    nationality: str = "domestic"
    include_hostel: bool = True
    cgpa: Optional[float] = None
    category: Optional[str] = None

class CalendarRequest(BaseModel):
    program: Optional[str] = None
    semester: Optional[str] = None
    query_type: str = "all"

class RAGRequest(BaseModel):
    query: str
    doc_type: Optional[str] = None
    top_k: int = 5

class FacultyRequest(BaseModel):
    department: Optional[str] = None
    name: Optional[str] = None
    course_code: Optional[str] = None

class SessionUpdateRequest(BaseModel):
    program: Optional[str] = None
    year: Optional[int] = None
    department: Optional[str] = None
    nationality: Optional[str] = None
    name: Optional[str] = None
    completed_courses: Optional[List[str]] = None


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize vector store on startup."""
    logger.info("Initializing University Assistant API...")
    try:
        initialize_vector_store()
        logger.info("Vector store ready.")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    return {"status": "University Assistant API is running", "version": "1.0.0"}

@app.get("/health", tags=["health"])
def health_check():
    try:
        from backend.rag.vector_store import get_vector_store
        store = get_vector_store()
        doc_count = store.count()
    except Exception:
        doc_count = -1

    cache_stats = get_cache_stats()
    return {
        "status": "healthy",
        "vector_store_docs": doc_count,
        "cache": cache_stats,
    }


# ── /chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest):
    """
    Main conversational endpoint. Routes to appropriate tools and LLM.
    Maintains session-level memory.
    """
    session_id = request.session_id or str(uuid.uuid4())
    try:
        agent = get_agent()
        result = agent.chat(session_id, request.message)
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            intent=result["intent"],
            tool_used=result["tool_used"],
            sources=result["sources"],
            student_profile=result["student_profile"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}", tags=["chat"])
def get_session(session_id: str):
    """Get current session/student profile."""
    memory = get_memory_manager(session_id)
    return memory.entity.to_dict()


@app.post("/session/{session_id}/update", tags=["chat"])
def update_session(session_id: str, request: SessionUpdateRequest):
    """Manually update student profile for a session."""
    memory = get_memory_manager(session_id)
    updates = {k: v for k, v in request.dict().items() if v is not None}
    memory.entity.update(**updates)
    memory.save()
    return {"status": "updated", "profile": memory.entity.to_dict()}


@app.delete("/session/{session_id}", tags=["chat"])
def delete_session(session_id: str):
    """Clear all memory for a session."""
    clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


# ── /course ────────────────────────────────────────────────────────────────────

@app.get("/course/{course_code}", tags=["courses"])
def get_course(course_code: str, completed_courses: str = ""):
    """Get course details by code. Optionally check prerequisites."""
    course = get_course_by_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course {course_code} not found")

    completed = [c.strip() for c in completed_courses.split(",") if c.strip()] if completed_courses else []
    prereq_check = check_prerequisites(course_code, completed)

    return {
        "course": course,
        "prerequisite_check": prereq_check,
    }


@app.post("/course/search", tags=["courses"])
def search_course(request: CourseRequest):
    """Search courses by keyword, program, year, or department."""
    if request.course_code:
        course = get_course_by_code(request.course_code)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        prereq = check_prerequisites(request.course_code, request.completed_courses or [])
        return {"courses": [course], "prerequisite_checks": [prereq]}

    results = search_courses(
        keyword=request.keyword,
        program=request.program,
        year=request.year,
    )
    return {"courses": results, "count": len(results)}


# ── /timetable ─────────────────────────────────────────────────────────────────

@app.post("/timetable", tags=["timetable"])
def get_timetable_endpoint(request: TimetableRequest):
    """Get weekly timetable for a program and year."""
    tt = get_timetable(request.program, request.year)
    if "error" in tt:
        raise HTTPException(status_code=404, detail=tt["error"])

    labs = get_lab_schedule(request.program, request.year)
    formatted = format_timetable(request.program, request.year)

    return {
        "program": request.program,
        "year": request.year,
        "timetable": tt,
        "lab_schedule": labs,
        "formatted": formatted,
    }


@app.get("/timetable/{program}/{year}", tags=["timetable"])
def get_timetable_simple(program: str, year: int):
    """Simple GET endpoint for timetable."""
    tt = get_timetable(program, year)
    if "error" in tt:
        raise HTTPException(status_code=404, detail=tt["error"])
    return {"program": program, "year": year, "timetable": tt}


# ── /fees ──────────────────────────────────────────────────────────────────────

@app.post("/fees", tags=["fees"])
def get_fees(request: FeesRequest):
    """Get fee breakdown and scholarship info."""
    fee_info = get_fee_breakdown(request.program, request.nationality, request.include_hostel)
    if "error" in fee_info:
        raise HTTPException(status_code=404, detail=fee_info["error"])

    scholarships = get_scholarships(program=request.program, nationality=request.nationality)

    eligible_scholarships = []
    if request.cgpa is not None:
        eligible_scholarships = check_scholarship_eligibility(
            program=request.program,
            cgpa=request.cgpa,
            category=request.category,
            nationality=request.nationality,
        )

    return {
        "fees": fee_info,
        "available_scholarships": scholarships,
        "eligible_scholarships": eligible_scholarships,
        "formatted_summary": format_fee_summary(request.program, request.nationality),
    }


@app.get("/fees/{program}", tags=["fees"])
def get_fees_simple(program: str, nationality: str = "domestic"):
    """Simple GET for fee structure."""
    fee_info = get_fee_breakdown(program, nationality)
    if "error" in fee_info:
        raise HTTPException(status_code=404, detail=fee_info["error"])
    return fee_info


# ── /calendar ──────────────────────────────────────────────────────────────────

@app.post("/calendar", tags=["calendar"])
def get_calendar(request: CalendarRequest):
    """Get academic calendar info — deadlines, exams, holidays."""
    info = get_calendar_info(
        program=request.program,
        query_type=request.query_type,
        semester=request.semester,
    )
    return info


@app.get("/calendar/registration", tags=["calendar"])
def get_registration_deadline(program: Optional[str] = None):
    """Get next registration deadline."""
    return {"message": get_next_registration_deadline(program)}


# ── /rag ───────────────────────────────────────────────────────────────────────

@app.post("/rag", tags=["rag"])
def rag_query(request: RAGRequest):
    """
    Direct RAG retrieval endpoint.
    Returns top-k relevant documents for a query.
    """
    retriever = get_retriever()
    results = retriever.retrieve_with_scores(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "results": results,
        "count": len(results),
    }


@app.post("/rag/context", tags=["rag"])
def get_rag_context(request: RAGRequest):
    """Get formatted RAG context string for a query."""
    retriever = get_retriever()
    context = retriever.format_context(request.query, top_k=request.top_k)
    return {"query": request.query, "context": context}


# ── /faculty ───────────────────────────────────────────────────────────────────

@app.post("/faculty", tags=["faculty"])
def get_faculty(request: FacultyRequest):
    """Get faculty information by department, name, or course code."""
    if request.name:
        from backend.tools.faculty import get_faculty_by_name
        faculty = get_faculty_by_name(request.name)
        if not faculty:
            raise HTTPException(status_code=404, detail=f"Faculty '{request.name}' not found")
        return {"faculty": [faculty]}

    if request.course_code:
        from backend.tools.faculty import get_faculty_for_course
        faculty = get_faculty_for_course(request.course_code)
        if not faculty:
            raise HTTPException(status_code=404, detail=f"No faculty found for course {request.course_code}")
        return {"faculty": [faculty]}

    if request.department:
        faculty_list = get_faculty_by_department(request.department)
        return {
            "department": request.department,
            "faculty": faculty_list,
            "count": len(faculty_list),
            "formatted": format_department_faculty(request.department),
        }

    # Return all departments
    return {"departments": get_all_departments()}


@app.get("/faculty/departments", tags=["faculty"])
def list_departments():
    """List all departments."""
    return {"departments": get_all_departments()}


# ── /campus ────────────────────────────────────────────────────────────────────

@app.get("/campus/{location}", tags=["campus"])
def get_campus_location(location: str):
    """Get info about a campus location."""
    info = get_building_info(location)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.get("/campus/directions/{from_loc}/{to_loc}", tags=["campus"])
def campus_directions(from_loc: str, to_loc: str):
    """Get walking directions between two campus locations."""
    directions = get_directions(from_loc, to_loc)
    return {"directions": directions}


# ── /support ───────────────────────────────────────────────────────────────────

@app.get("/support/{category}", tags=["support"])
def student_support(category: str):
    """Get student support information (hostel, library, medical, counseling)."""
    info = get_support_info(category)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.get("/support/emergency/contacts", tags=["support"])
def emergency_contacts():
    """Get all emergency contact numbers."""
    return {"contacts": get_emergency_contacts()}


# ── /admin (cache management) ──────────────────────────────────────────────────

@app.get("/admin/cache/stats", tags=["admin"])
def cache_stats():
    """Get cache statistics."""
    return get_cache_stats()


@app.delete("/admin/cache", tags=["admin"])
def clear_cache(namespace: Optional[str] = None):
    """Clear cache (optionally by namespace)."""
    invalidate_cache(namespace)
    return {"status": "cleared", "namespace": namespace or "all"}


@app.post("/admin/rag/reload", tags=["admin"])
def reload_rag(background_tasks: BackgroundTasks):
    """Trigger a background reload of the RAG vector store."""
    background_tasks.add_task(initialize_vector_store, force_reload=True)
    return {"status": "RAG reload triggered in background"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
