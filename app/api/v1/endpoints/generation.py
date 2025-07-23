from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.schemas.generation import (
    GenerationRequest, 
    GenerationResponse, 
    LessonPlanRequest,
    LessonPlanResponse
)
from app.services.watsonx_service import WatsonXService

# Create router
router = APIRouter(prefix="/generate", tags=["Generation"])

# Dependency to get service
def get_watson_service():
    return WatsonXService()

# Keep your existing endpoint
@router.post(
    "/",
    response_model=GenerationResponse,
    summary="Generate content and quiz",
    description="Generate educational content and quiz questions based on the given topic, optionally enhanced with web search results"
)
async def generate_content_and_quiz(
    request: GenerationRequest,
    service: WatsonXService = Depends(get_watson_service)
):
    """Generate content and quiz questions for a topic"""
    try:
        result = await service.generate_content_and_quiz(
            topic=request.topic,
            use_web_context=request.use_web_context
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating content and quiz: {str(e)}"
        )

# Add new endpoint for lesson plans
@router.post(
    "/lesson-plan",
    response_model=LessonPlanResponse,
    summary="Generate lesson plan",
    description="Generate a detailed lesson plan with quiz questions based on topic, duration, grade level, and teaching style"
)
async def generate_lesson_plan(
    request: LessonPlanRequest,
    service: WatsonXService = Depends(get_watson_service)
):
    """Generate a lesson plan with assessment questions"""
    try:
        result = await service.generate_lesson_plan(
            topic=request.topic,
            duration=request.duration,
            grade_level=request.grade_level,
            style=request.style
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating lesson plan: {str(e)}"
        )
