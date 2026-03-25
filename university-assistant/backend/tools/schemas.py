from pydantic import BaseModel, Field

class CourseQuery(BaseModel):
    course_name: str = Field(..., description="Name of the course")

class StudentQuery(BaseModel):
    student_id: str = Field(..., description="Student ID")

class DepartmentQuery(BaseModel):
    department: str = Field(..., description="Department name")


class DateQuery(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class FeeQuery(BaseModel):
    program : str
    department : str
    year : int