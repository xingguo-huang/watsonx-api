from pydantic import BaseModel, Field
from typing import List, Optional


class GenerationRequest(BaseModel):
    topic: str = Field(..., description="Topic for content generation", min_length=2)
    

class Option(BaseModel):
    text: str
    is_correct: bool


class Question(BaseModel):
    question_text: str
    options: List[Option]


class GenerationResponse(BaseModel):
    content: str
    questions: List[Question]
    topic: str
