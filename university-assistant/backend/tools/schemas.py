from pydantic import BaseModel, Field

class CourseQuery(BaseModel):
    course_name: str = Field(..., description="The exact name or subject of the course to look up, e.g., 'Machine Learning', 'AI101'")

class StudentQuery(BaseModel):
    student_id: str = Field(..., description="The student's unique identification number (e.g., 'S001', '12345')")

class DepartmentQuery(BaseModel):
    department: str = Field(..., description="The name of the university department, e.g., 'Computer Science'")

class DateQuery(BaseModel):
    date: str = Field(..., description="The target date strictly in YYYY-MM-DD format")

class FeeQuery(BaseModel):
    program: str = Field(..., description="The degree program strictly without punctuation (e.g., 'BTech', 'MSc', 'MBA')")
    department: str = Field(..., description="The specific department (e.g., 'CSE', 'Mechanical')")
    year: int = Field(..., description="The numeric year of study, e.g., 1, 2, 3, 4")