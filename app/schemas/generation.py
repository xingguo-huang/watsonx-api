from pydantic import BaseModel, Field
from typing import List, Optional

# Option in a multiple choice question
class Option(BaseModel):
    text: str
    is_correct: bool

# Question with multiple choice options
class Question(BaseModel):
    question_text: str
    options: List[Option]

# Phase in a lesson plan
class Phase(BaseModel):
    phase: str = Field(..., description="Name of this phase of the lesson")
    duration: str = Field(..., description="Duration of this phase (e.g., '10 minutes')")
    purpose: str = Field(..., description="What students will achieve in this phase")
    description: str = Field(..., description="Detailed explanation of this phase")

# Lesson plan structure
class LessonPlan(BaseModel):
    objectives: List[str] = Field(..., description="Learning objectives for the lesson")
    outline: List[Phase] = Field(..., description="Phases of the lesson")

# Original content generation request
class GenerationRequest(BaseModel):
    topic: str = Field(..., description="Topic to generate content about")
    parameters: Optional[dict] = Field(default_factory=dict, description="Optional generation parameters")

# Original content generation response
class GenerationResponse(BaseModel):
    content: str
    questions: List[Question]
    topic: str

# New lesson plan generation request
class LessonPlanRequest(BaseModel):
    topic: str = Field(..., description="The main topic for the lesson")
    duration: int = Field(..., description="Total duration of the lesson in minutes")
    grade_level: str = Field(..., description="Target grade level (e.g., '5th Grade', 'High School')")
    style: str = Field(..., description="Teaching style(s) to use")

# New lesson plan generation response
class LessonPlanResponse(BaseModel):
    lesson_plan: LessonPlan
    questions: List[Question] = Field(default_factory=list)
    topic: str
