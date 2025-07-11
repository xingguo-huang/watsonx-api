import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.settings import settings

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for generating educational content and quizzes using IBM WatsonX.ai",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API v1 router with prefix
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Root endpoint
    @application.get("/", tags=["Root"])
    async def root():
        return {
            "message": "WatsonX.ai Content & Quiz Generation API",
            "docs": "/docs",
        }

    return application

# Create FastAPI application
app = create_application()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
