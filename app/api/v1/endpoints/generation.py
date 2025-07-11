from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.watsonx_service import WatsonXService

# Create router with prefix and tag
router = APIRouter(prefix="/generate", tags=["Generation"])

# Dependency to get service
def get_watson_service():
    return WatsonXService()

@router.post(
    "/",
    response_model=GenerationResponse,
    summary="Generate content and quiz",
    description="Generate educational content and quiz questions based on the given topic"
)
async def generate_content_and_quiz(
    request: GenerationRequest,
    service: WatsonXService = Depends(get_watson_service)
):
    """Generate content and quiz questions for a topic"""
    try:
        result = await service.generate_content_and_quiz(topic=request.topic)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating content and quiz: {str(e)}"
        )

@router.get(
    "/health",
    summary="Health check endpoint"
)
async def health_check():
    """Check if the service is healthy"""
    return {"status": "healthy", "service": "watsonx-generation"}
