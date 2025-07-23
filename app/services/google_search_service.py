import requests
import os
from typing import Dict, List, Any, Optional

class GoogleSearchService:
    def __init__(self):
        """Initialize the Google Search service with API credentials."""
        from app.core.settings import settings
        
        self.api_key = settings.GOOGLE_API_KEY
        self.cse_id = settings.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num_results: int = 5) -> str:
        """Search Google for the given query and return formatted results."""
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10)  # Google API limits to 10 results per page
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            data = response.json()

            if "items" not in data:
                return "No search results found for the query."

            results = []
            for i, item in enumerate(data["items"], 1):
                title = item.get("title", "No title")
                link = item.get("link", "")
                snippet = item.get("snippet", "No description available")
                
                results.append(f"Source {i}: {title}\nURL: {link}\nSummary: {snippet}")
            
            return "\n\n".join(results)
            
        except Exception as e:
            print(f"Error during Google search: {str(e)}")
            return f"Error performing search: {str(e)}"