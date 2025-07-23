from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    PROJECT_NAME: str = "WatsonX.ai Content Generator"
    API_V1_STR: str = "/api/v1"
    
    # Watson X AI settings
    WATSON_API_URL: str
    WATSON_API_KEY: str
    WATSON_PROJECT_ID: str
    
    # LLM Model settings
    MODEL_ID: str = "ibm/granite-3-8b-instruct"
    MAX_NEW_TOKENS: int = 1024
    MIN_NEW_TOKENS: int = 10
    TEMPERATURE: float = 0.1
    TOP_K: int = 20
    
    # Google Search API settings
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()
