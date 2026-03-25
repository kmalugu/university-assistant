from backend.tools.course_lookup import get_course_info
from backend.tools.calendar import get_academic_events

print(get_course_info.invoke({"course_name": "Machine Learning"}))
print(get_academic_events.invoke({"date": "2026-04-01"}))