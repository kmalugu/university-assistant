"""
University Student Information & Guidance Assistant
Streamlit Frontend — Chat + Course Lookup + Timetable + Fees + Calendar + Map
"""
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime

import streamlit as st
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="UniAssist — Student Guidance AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
html, body, [data-testid="stAppViewContainer"] {
    background: #0f1117;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b27 !important;
    border-right: 1px solid #2a2f3f;
}

/* Cards */
.card {
    background: #1a1f2e;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 14px;
}
.card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #7eb3ff;
    margin-bottom: 8px;
}

/* Chat bubbles */
.user-bubble {
    background: #1a3a5c;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 15%;
    color: #e0f0ff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.bot-bubble {
    background: #1e2a3a;
    border: 1px solid #2a4060;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 15% 8px 0;
    color: #d0e8ff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.intent-badge {
    display: inline-block;
    background: #0d2137;
    border: 1px solid #1a4a7a;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    color: #7eb3ff;
    margin-top: 6px;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1a2340 0%, #0f1a2e 100%);
    border: 1px solid #2a3a5a;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #7eb3ff;
}
.metric-label {
    font-size: 0.8rem;
    color: #8898aa;
    margin-top: 4px;
}

/* Tables */
.styled-table { width: 100%; border-collapse: collapse; }
.styled-table th {
    background: #1a2a45;
    color: #7eb3ff;
    padding: 10px;
    text-align: left;
    font-size: 0.85rem;
}
.styled-table td {
    padding: 9px 10px;
    border-bottom: 1px solid #1e2a3a;
    font-size: 0.85rem;
    color: #c0d4e8;
}
.styled-table tr:hover td { background: #1a2335; }

/* Pill tags */
.pill {
    display: inline-block;
    background: #0d2137;
    border: 1px solid #1a4a7a;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #7eb3ff;
    margin: 2px;
}
.pill-green { background: #0d2a1a; border-color: #1a5a30; color: #4caf88; }
.pill-red { background: #2a1a1a; border-color: #5a2a2a; color: #e07070; }

/* Divider */
hr.custom { border: none; border-top: 1px solid #2a3050; margin: 16px 0; }

/* Input area */
[data-testid="stChatInputContainer"] {
    background: #1a1f2e !important;
    border-top: 1px solid #2a3050;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {}
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Chat"


# ── API helpers ────────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "⚠️ Cannot connect to the backend API. Make sure it's running on port 8000."}
    except Exception as e:
        return {"error": str(e)}


def api_get(endpoint: str, params: dict = None) -> dict:
    try:
        r = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "⚠️ Cannot connect to backend API."}
    except Exception as e:
        return {"error": str(e)}


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 UniAssist")
    st.markdown("<p style='color:#8898aa;font-size:0.85rem'>AI-Powered Campus Guide</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Student profile form
    st.markdown("### 👤 My Profile")
    with st.form("profile_form"):
        name = st.text_input("Your Name", placeholder="e.g. Arjun Sharma")
        col1, col2 = st.columns(2)
        with col1:
            program = st.selectbox("Program", ["", "BTech", "MBA", "MSc", "PhD"])
        with col2:
            year = st.selectbox("Year", ["", 1, 2, 3, 4])
        department = st.selectbox(
            "Department",
            ["", "Computer Science", "Data Science", "Mathematics", "Management", "Research"]
        )
        nationality = st.radio("Nationality", ["domestic", "international"], horizontal=True)
        completed = st.text_input("Completed Courses (comma-sep)", placeholder="CS101, MATH101")

        if st.form_submit_button("💾 Save Profile", use_container_width=True):
            payload = {
                "name": name or None,
                "program": program or None,
                "year": int(year) if year else None,
                "department": department or None,
                "nationality": nationality,
                "completed_courses": [c.strip() for c in completed.split(",") if c.strip()] if completed else None,
            }
            result = api_post(f"/session/{st.session_state.session_id}/update", payload)
            if "error" not in result:
                st.session_state.student_profile = result.get("profile", {})
                st.success("Profile saved!")
            else:
                st.error(result["error"])

    st.markdown("---")

    # Quick navigation
    st.markdown("### 🧭 Quick Links")
    quick_prompts = [
        ("📅 Registration deadline", "When does course registration close?"),
        ("📚 Course prerequisites", "What are the prerequisites for ML301?"),
        ("💰 Fee structure", "Show me BTech fee breakdown"),
        ("🗓️ My timetable", "Show my weekly timetable"),
        ("🏫 Faculty info", "Who teaches AI in Computer Science department?"),
        ("🗺️ Library location", "Where is the library and what are its timings?"),
        ("🎓 Scholarships", "What scholarships are available for BTech?"),
        ("🏥 Health center", "What are the health center timings?"),
    ]
    for label, prompt in quick_prompts:
        if st.button(label, use_container_width=True, key=f"qp_{label}"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                result = api_post("/chat", {
                    "session_id": st.session_state.session_id,
                    "message": prompt,
                })
            if "error" not in result:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["response"],
                    "intent": result.get("intent", ""),
                    "tool": result.get("tool_used", ""),
                    "sources": result.get("sources", []),
                })
                st.session_state.student_profile = result.get("student_profile", {})
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.student_profile = {}
        st.rerun()

    # Session info
    st.markdown(f"<p style='color:#4a5568;font-size:0.7rem'>Session: {st.session_state.session_id[:12]}...</p>",
                unsafe_allow_html=True)


# ── Main area ──────────────────────────────────────────────────────────────────

st.markdown("## 🎓 University Student Guidance Assistant")

tabs = st.tabs(["💬 Chat", "📚 Courses", "🗓️ Timetable", "💰 Fees & Aid", "📅 Calendar", "🏫 Faculty", "🗺️ Campus Map"])

# ════════════════════════════════════════════════════════
# TAB 1: CHAT
# ════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("#### Ask me anything about your academics, campus, or university life!")

    # Display profile summary bar if filled
    profile = st.session_state.student_profile
    if profile.get("program") or profile.get("name"):
        cols = st.columns(5)
        items = [
            ("👤", profile.get("name", "—")),
            ("🎓", profile.get("program", "—")),
            ("📅", f"Year {profile.get('year', '—')}"),
            ("🏛️", profile.get("department", "—")),
            ("🌍", profile.get("nationality", "domestic").title()),
        ]
        for col, (icon, val) in zip(cols, items):
            col.markdown(
                f"<div class='metric-card'><div class='metric-value' style='font-size:1.1rem'>{icon}</div>"
                f"<div class='metric-label'>{val}</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("")

    # Chat history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div class='card' style='text-align:center;padding:40px'>
                <div style='font-size:3rem'>🎓</div>
                <div style='font-size:1.2rem;color:#7eb3ff;margin-top:12px'>Welcome to UniAssist!</div>
                <div style='color:#8898aa;margin-top:8px'>
                    I can help you with courses, timetables, fees, deadlines, faculty info, and campus navigation.<br>
                    Try the quick links on the left or type your question below!
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='user-bubble'>🧑‍🎓 {msg['content']}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    content = msg["content"].replace("\n", "<br>")
                    intent_badge = ""
                    if msg.get("intent"):
                        intent_badge = f"<div class='intent-badge'>🔍 {msg['intent']}</div>"
                        if msg.get("tool"):
                            intent_badge += f"<div class='intent-badge'>🛠️ {msg['tool']}</div>"
                    st.markdown(
                        f"<div class='bot-bubble'>🤖 {content}{intent_badge}</div>",
                        unsafe_allow_html=True
                    )
                    if msg.get("sources"):
                        with st.expander("📎 Sources", expanded=False):
                            for s in msg["sources"]:
                                st.caption(f"• {s}")

    # Chat input
    if user_input := st.chat_input("Type your question here...", key="chat_input"):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("UniAssist is thinking..."):
            result = api_post("/chat", {
                "session_id": st.session_state.session_id,
                "message": user_input,
            })
        if "error" in result:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["error"],
                "intent": "error",
                "tool": "",
                "sources": [],
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["response"],
                "intent": result.get("intent", ""),
                "tool": result.get("tool_used", ""),
                "sources": result.get("sources", []),
            })
            st.session_state.student_profile = result.get("student_profile", {})
        st.rerun()


# ════════════════════════════════════════════════════════
# TAB 2: COURSES
# ════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("#### 📚 Course Lookup & Prerequisites Checker")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("##### Search")
        lookup_type = st.radio("Search by", ["Course Code", "Keyword / Program"], horizontal=True)

        if lookup_type == "Course Code":
            course_code = st.text_input("Course Code", placeholder="e.g. AI101", key="cc_code").upper()
            completed = st.text_input("Completed Courses (for prereq check)", placeholder="CS101, MATH101")
            if st.button("🔍 Look Up Course", use_container_width=True):
                if course_code:
                    result = api_get(f"/course/{course_code}", {"completed_courses": completed})
                    st.session_state["course_result"] = result
        else:
            keyword = st.text_input("Keyword", placeholder="e.g. Machine Learning")
            prog_filter = st.selectbox("Program", ["", "BTech", "MBA", "MSc", "PhD"], key="prog_search")
            year_filter = st.selectbox("Year", ["", 1, 2, 3, 4], key="year_search")
            if st.button("🔍 Search Courses", use_container_width=True):
                result = api_post("/course/search", {
                    "keyword": keyword or None,
                    "program": prog_filter or None,
                    "year": int(year_filter) if year_filter else None,
                })
                st.session_state["course_result"] = result

    with col_right:
        result = st.session_state.get("course_result", {})
        if "error" in result:
            st.error(result["error"])
        elif "course" in result:
            c = result["course"]
            prereq = result.get("prerequisite_check", {})
            st.markdown(f"""
            <div class='card'>
                <div class='card-title'>{c['code']} — {c['title']}</div>
                <div style='margin-bottom:10px'>
                    <span class='pill'>{c['credits']} Credits</span>
                    <span class='pill'>Year {c['year']}</span>
                    <span class='pill'>{c['department']}</span>
                    {''.join(f"<span class='pill'>{p}</span>" for p in c.get('programs',[]))}
                </div>
                <p style='color:#a0b4cc'>{c.get('description','')}</p>
                <hr class='custom'>
                <b style='color:#7eb3ff'>Prerequisites:</b> {', '.join(c.get('prerequisites',[])) or 'None'}<br>
                <b style='color:#7eb3ff'>Timings:</b> {c.get('lecture_timings','TBA')} — Room {c.get('classroom','TBA')}<br>
                {'<b style="color:#7eb3ff">Lab:</b> ' + c['lab_timings'] + '<br>' if c.get('lab_timings') else ''}
                <b style='color:#7eb3ff'>Faculty:</b> {c.get('faculty','TBA')}
            </div>
            """, unsafe_allow_html=True)

            if prereq:
                eligible = prereq.get("eligible", True)
                badge_class = "pill-green" if eligible else "pill-red"
                icon = "✅" if eligible else "❌"
                st.markdown(
                    f"<div class='card'><b>Prerequisite Check:</b> "
                    f"<span class='{badge_class}'>{icon} {prereq.get('message','')}</span></div>",
                    unsafe_allow_html=True
                )

            st.markdown("**Syllabus Topics:**")
            topics = c.get("syllabus", [])
            cols = st.columns(3)
            for i, topic in enumerate(topics):
                cols[i % 3].markdown(f"<span class='pill'>{topic}</span>", unsafe_allow_html=True)

        elif "courses" in result:
            courses = result["courses"]
            st.markdown(f"**{len(courses)} course(s) found:**")
            for c in courses:
                with st.expander(f"{c['code']} — {c['title']} ({c['credits']} cr)"):
                    st.markdown(f"""
                    **Department:** {c['department']} | **Year:** {c['year']}  
                    **Prerequisites:** {', '.join(c.get('prerequisites',[])) or 'None'}  
                    **Description:** {c.get('description','')}  
                    **Timings:** {c.get('lecture_timings','TBA')} — Room {c.get('classroom','TBA')}  
                    **Faculty:** {c.get('faculty','TBA')}
                    """)
        elif not result:
            st.info("Use the search panel on the left to find courses.")


# ════════════════════════════════════════════════════════
# TAB 3: TIMETABLE
# ════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("#### 🗓️ Weekly Timetable Viewer")
    col1, col2, col3 = st.columns(3)
    with col1:
        tt_program = st.selectbox("Program", ["BTech", "MBA", "MSc", "PhD"], key="tt_prog")
    with col2:
        tt_year = st.selectbox("Year", [1, 2, 3, 4], key="tt_year")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📅 Load Timetable", use_container_width=True):
            result = api_post("/timetable", {"program": tt_program, "year": tt_year})
            st.session_state["tt_result"] = result

    tt_result = st.session_state.get("tt_result", {})
    if "error" in tt_result:
        st.error(tt_result.get("error", "Error loading timetable"))
    elif "timetable" in tt_result:
        tt = tt_result["timetable"]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        type_colors = {"Lecture": "#1a3a5c", "Lab": "#1a3a2a", "Tutorial": "#3a2a1a", "Elective": "#2a1a3a",
                       "Project": "#2a2a1a", "Free": "#1a2a2a", "Activity": "#1a1a3a", "Review": "#2a1a1a"}

        for day in days:
            slots = tt.get(day, [])
            if not slots:
                continue
            st.markdown(f"**{day}**")
            cols = st.columns(max(len(slots), 1))
            for i, slot in enumerate(slots):
                bg = type_colors.get(slot.get("type", ""), "#1a2a3a")
                building = f" · {slot['building']}" if slot.get("building") else ""
                cols[i].markdown(f"""
                <div style='background:{bg};border:1px solid #2a3a5a;border-radius:8px;
                            padding:10px;font-size:0.82rem;height:100%'>
                    <div style='color:#7eb3ff;font-weight:700'>{slot['time']}</div>
                    <div style='color:#c0d4e8;margin:4px 0'>{slot['subject']}</div>
                    <div style='color:#8898aa'>{slot['room']}{building}</div>
                    <div style='color:#5a6a8a;font-size:0.75rem'>[{slot['type']}]</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("")

        # Lab schedule summary
        labs = tt_result.get("lab_schedule", [])
        if labs:
            st.markdown("---")
            st.markdown("##### 🧪 Lab Sessions Summary")
            lab_rows = "".join(
                f"<tr><td>{l['day']}</td><td>{l['time']}</td><td>{l['subject']}</td><td>{l['room']}</td></tr>"
                for l in labs
            )
            st.markdown(
                f"<table class='styled-table'><thead><tr><th>Day</th><th>Time</th><th>Subject</th><th>Room</th></tr></thead>"
                f"<tbody>{lab_rows}</tbody></table>",
                unsafe_allow_html=True
            )
    else:
        st.info("Select your program and year, then click 'Load Timetable'.")


# ════════════════════════════════════════════════════════
# TAB 4: FEES & SCHOLARSHIPS
# ════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("#### 💰 Fee Structure & Financial Aid")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fee_prog = st.selectbox("Program", ["BTech", "MBA", "MSc", "PhD"], key="fee_prog")
    with c2:
        fee_nat = st.selectbox("Nationality", ["domestic", "international"], key="fee_nat")
    with c3:
        fee_cgpa = st.number_input("Your CGPA (for scholarship check)", 0.0, 10.0, step=0.1, key="fee_cgpa")
    with c4:
        fee_cat = st.selectbox("Category", ["general", "sc", "st", "obc"], key="fee_cat")

    if st.button("💳 Get Fee Details", use_container_width=False):
        result = api_post("/fees", {
            "program": fee_prog,
            "nationality": fee_nat,
            "cgpa": fee_cgpa if fee_cgpa > 0 else None,
            "category": fee_cat if fee_cat != "general" else None,
        })
        st.session_state["fee_result"] = result

    fee_result = st.session_state.get("fee_result", {})
    if "error" in fee_result:
        st.error(fee_result["error"])
    elif "fees" in fee_result:
        fees = fee_result["fees"]
        fd = fees.get("fee_breakdown", {})

        # Fee breakdown cards
        st.markdown("##### 📊 Fee Breakdown (per semester)")
        fee_items = [
            ("Tuition", fd.get("tuition_per_semester", fd.get("tuition_per_year", 0))),
            ("Hostel", fd.get("hostel_per_semester", 0)),
            ("Mess", fd.get("mess_per_semester", 0)),
            ("Library", fd.get("library_fee", 0)),
            ("Lab", fd.get("lab_fee", 0)),
            ("Medical", fd.get("medical_fee", 0)),
        ]
        fee_items = [(k, v) for k, v in fee_items if v]
        cols = st.columns(len(fee_items))
        for col, (label, amount) in zip(cols, fee_items):
            col.markdown(
                f"<div class='metric-card'><div class='metric-value'>₹{amount:,}</div>"
                f"<div class='metric-label'>{label}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown(f"""
        <div class='card' style='margin-top:14px'>
            <b style='color:#7eb3ff'>💳 Total/Semester (with hostel):</b> {fees.get('total_per_semester','N/A')}  
            <br><b style='color:#7eb3ff'>⏰ Payment Deadline:</b> {fees.get('payment_deadline','N/A')}  
            <br><b style='color:#ff8888'>⚠️ Late Fine:</b> {fees.get('late_fine_per_day','N/A')}
        </div>
        """, unsafe_allow_html=True)

        # Eligible scholarships
        eligible = fee_result.get("eligible_scholarships", [])
        all_scholarships = fee_result.get("available_scholarships", [])

        st.markdown("---")
        st.markdown("##### 🎓 Scholarships")
        col_e, col_a = st.columns(2)
        with col_e:
            st.markdown("**You may be eligible for:**")
            if eligible:
                for s in eligible:
                    st.markdown(f"""
                    <div class='card'>
                        <div class='card-title'>🏆 {s['scholarship']}</div>
                        <div style='color:#4caf88'>Benefit: {s['benefit']}</div>
                        <div style='color:#8898aa;font-size:0.8rem'>Deadline: {s['application_deadline']}</div>
                        <div style='color:#8898aa;font-size:0.8rem'>Renewal: {s['renewal']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Enter your CGPA and category to check eligibility.")

        with col_a:
            st.markdown("**All Available Scholarships:**")
            for s in all_scholarships:
                with st.expander(s["name"]):
                    st.markdown(f"""
                    **Benefit:** {s['benefit']}  
                    **Eligibility:** {s['eligibility']}  
                    **Deadline:** {s['application_deadline']}  
                    **Programs:** {', '.join(s['programs'])}
                    """)
    else:
        st.info("Select your program and click 'Get Fee Details' to view the breakdown.")


# ════════════════════════════════════════════════════════
# TAB 5: CALENDAR
# ════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("#### 📅 Academic Calendar & Important Dates")

    col1, col2 = st.columns(2)
    with col1:
        cal_prog = st.selectbox("Program", ["", "BTech", "MBA", "MSc", "PhD"], key="cal_prog")
    with col2:
        cal_sem = st.radio("Semester", ["odd", "even"], horizontal=True, key="cal_sem")

    result = api_post("/calendar", {
        "program": cal_prog or None,
        "semester": cal_sem,
        "query_type": "all",
    })

    if "error" in result:
        st.error(result["error"])
    else:
        # Upcoming deadlines
        upcoming = result.get("upcoming_deadlines", [])
        if upcoming:
            st.markdown("##### ⏰ Upcoming Deadlines")
            cols = st.columns(min(len(upcoming), 4))
            for col, d in zip(cols, upcoming):
                urgency_color = "#ff6b6b" if d["days_left"] <= 7 else "#ffa500" if d["days_left"] <= 14 else "#4caf88"
                col.markdown(
                    f"<div class='metric-card'>"
                    f"<div class='metric-value' style='color:{urgency_color}'>{d['days_left']}</div>"
                    f"<div class='metric-label'>days left</div>"
                    f"<div style='font-size:0.78rem;color:#c0d4e8;margin-top:6px'>{d['event']}</div>"
                    f"<div style='font-size:0.72rem;color:#8898aa'>{d['date']}</div></div>",
                    unsafe_allow_html=True
                )

        st.markdown("---")
        col_reg, col_exam = st.columns(2)

        with col_reg:
            st.markdown("##### 📝 Registration Window")
            reg = result.get("registration", {})
            if reg:
                st.markdown(f"""
                <div class='card'>
                    <div>📅 <b>Opens:</b> {reg.get('opens','N/A')}</div>
                    <div>🔒 <b>Closes:</b> {reg.get('closes','N/A')}</div>
                    <div>⏱️ <b>Late registration until:</b> {reg.get('late_registration_until','N/A')}</div>
                    <div style='color:#ff8888'>💸 Late fee: {reg.get('late_fee','N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_exam:
            st.markdown("##### 📖 Exam Schedule")
            ias = result.get("internal_exams", [])
            ese = result.get("end_semester_exams", {})
            for ia in ias:
                st.markdown(
                    f"<div class='card'><b>{ia['name']}</b>: {ia['start']} – {ia['end']}</div>",
                    unsafe_allow_html=True
                )
            if ese:
                st.markdown(
                    f"<div class='card'><b>End Semester Exams</b>: {ese.get('start','?')} – {ese.get('end','?')}"
                    f"<br>Results: {result.get('result_declaration','TBA')}</div>",
                    unsafe_allow_html=True
                )

        # Holidays table
        holidays = result.get("holidays", [])
        if holidays:
            st.markdown("---")
            st.markdown("##### 🏖️ Holidays")
            rows = "".join(
                f"<tr><td>{h['date']}</td><td>{h['name']}</td></tr>" for h in holidays
            )
            st.markdown(
                f"<table class='styled-table'><thead><tr><th>Date</th><th>Holiday</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>",
                unsafe_allow_html=True
            )

        # Events
        events = result.get("events", [])
        if events:
            st.markdown("---")
            st.markdown("##### 🎉 Campus Events")
            for ev in events:
                st.markdown(f"• **{ev['date']}** — {ev['name']}")


# ════════════════════════════════════════════════════════
# TAB 6: FACULTY
# ════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("#### 🏫 Faculty Directory")

    fac_dept = st.selectbox(
        "Select Department",
        ["", "Computer Science", "Data Science", "Mathematics", "Management", "Research"],
        key="fac_dept"
    )
    fac_name = st.text_input("Or search by name", placeholder="e.g. Dr. Priya", key="fac_name")

    if st.button("🔍 Find Faculty", use_container_width=False):
        if fac_dept:
            result = api_post("/faculty", {"department": fac_dept})
        elif fac_name:
            result = api_post("/faculty", {"name": fac_name})
        else:
            result = api_get("/faculty/departments")
        st.session_state["fac_result"] = result

    fac_result = st.session_state.get("fac_result", {})
    if "error" in fac_result:
        st.error(fac_result["error"])
    elif "faculty" in fac_result:
        faculty_list = fac_result["faculty"]
        st.markdown(f"**{len(faculty_list)} faculty member(s) found:**")
        for f in faculty_list:
            with st.expander(f"👤 {f['name']} — {f['designation']} ({f['department']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    📧 **Email:** {f['email']}  
                    📞 **Phone:** {f['phone']}  
                    🏢 **Office:** {f['office']}
                    """)
                with col2:
                    st.markdown(f"""
                    🕐 **Consultation:** {f['consultation_hours']}  
                    🔬 **Specialization:** {f.get('specialization','')}  
                    📚 **Courses:** {', '.join(f.get('courses',[])) or 'N/A'}
                    """)
    elif "departments" in fac_result:
        depts = fac_result["departments"]
        st.markdown("**All Departments:**")
        for d in depts:
            with st.expander(f"🏫 {d['name']}"):
                st.markdown(f"""
                **HOD:** {d['hod']}  
                **Location:** {d['location']}  
                📞 {d['phone']} | 📧 {d['email']}
                """)
    else:
        st.info("Select a department or search by name to find faculty.")


# ════════════════════════════════════════════════════════
# TAB 7: CAMPUS MAP
# ════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("#### 🗺️ Campus Navigation")

    map_col1, map_col2 = st.columns([1, 2])
    with map_col1:
        st.markdown("##### 📍 Find a Location")
        location_query = st.text_input("Building / Facility", placeholder="e.g. library, cafeteria, CS Block")
        if st.button("🔍 Find", key="find_location"):
            result = api_get(f"/campus/{location_query.replace(' ', '%20')}")
            st.session_state["map_result"] = result

        st.markdown("---")
        st.markdown("##### 🧭 Get Directions")
        from_loc = st.text_input("From", placeholder="e.g. main gate")
        to_loc = st.text_input("To", placeholder="e.g. library")
        if st.button("Get Directions 🗺️"):
            result = api_get(f"/campus/directions/{from_loc.replace(' ','%20')}/{to_loc.replace(' ','%20')}")
            if "directions" in result:
                st.session_state["directions_result"] = result["directions"]

    with map_col2:
        # Directions
        if "directions_result" in st.session_state:
            st.markdown(
                f"<div class='card'>{st.session_state['directions_result']}</div>",
                unsafe_allow_html=True
            )

        # Location info
        map_result = st.session_state.get("map_result", {})
        if "error" in map_result:
            st.error(map_result["error"])
        elif map_result:
            st.markdown(f"""
            <div class='card'>
                <div class='card-title'>📍 {map_result.get('building_name', location_query.title())}</div>
                <div>{map_result.get('description','')}</div>
                {'<div>🕐 <b>Hours:</b> ' + map_result['hours'] + '</div>' if map_result.get('hours') else ''}
                {'<div>🔧 <b>Facilities:</b> ' + ', '.join(map_result['facilities']) + '</div>' if map_result.get('facilities') else ''}
                {'<div>📞 <b>Contact:</b> ' + map_result['contact'] + '</div>' if map_result.get('contact') else ''}
            </div>
            """, unsafe_allow_html=True)

        # Always show campus overview
        st.markdown("##### 🏫 Campus Key Locations")
        locations = {
            "📚 Library": "Central campus — 8 AM to 10 PM",
            "🖥️ CS Block": "East wing — Labs, Faculty offices",
            "📊 DS Block": "Adjacent to CS Block",
            "🎓 MBA Block": "West wing — Classrooms & Lounge",
            "⚗️ Research Block": "Behind Library",
            "📖 Lecture Halls": "Center of campus (LH-101 to LH-401)",
            "🏋️ Sports Complex": "South campus — 6 AM to 9 PM",
            "🏥 Health Center": "Near Main Gate — 24x7 Emergency",
            "🍽️ Cafeteria": "Central Block — 7:30 AM to 9 PM",
            "🏠 Hostels (Boys)": "North campus — Block A, B, C",
            "🏠 Hostels (Girls)": "South campus — Block D, E",
            "🏦 ATM": "Main Gate / Library / Hostel Zone",
        }
        cols = st.columns(3)
        for i, (loc, desc) in enumerate(locations.items()):
            cols[i % 3].markdown(
                f"<div class='card' style='padding:10px'>"
                f"<b>{loc}</b><br>"
                f"<span style='color:#8898aa;font-size:0.8rem'>{desc}</span></div>",
                unsafe_allow_html=True
            )
