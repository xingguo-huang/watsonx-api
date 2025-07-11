from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from langchain_ibm import WatsonxLLM
from ibm_watsonx_ai import Credentials
import json
from typing import List, Dict, Any
import re

from app.core.settings import settings
from app.schemas.generation import Question, Option
from app.prompts.templates import COMBINED_GENERATION_PROMPT


class WatsonXService:
    def __init__(self):
        # Initialize Watson credentials
        self.credentials = Credentials(
            url=settings.WATSON_API_URL,
            api_key=settings.WATSON_API_KEY
        )
        
        # Set model parameters
        self.parameters = {
            GenTextParamsMetaNames.MAX_NEW_TOKENS: settings.MAX_NEW_TOKENS,
            GenTextParamsMetaNames.MIN_NEW_TOKENS: settings.MIN_NEW_TOKENS,
            GenTextParamsMetaNames.TEMPERATURE: settings.TEMPERATURE,
            GenTextParamsMetaNames.TOP_K: settings.TOP_K,
        }
        
        # Initialize WatsonX LLM
        self.llm = WatsonxLLM(
            url=settings.WATSON_API_URL,
            apikey=settings.WATSON_API_KEY,
            project_id=settings.WATSON_PROJECT_ID,
            model_id=settings.MODEL_ID,
            params=self.parameters
        )

    async def generate_content_and_quiz(self, topic: str) -> Dict[str, Any]:
        """Generate both content and quiz questions based on the given topic"""
        
        # Create the prompt with instructions to generate both content and quiz
        # prompt = (
        #     f"Topic: {topic}\n\n"
        #     "1. Generate a ~200 word educational paragraph about this topic.\n"
        #     "2. Based on the paragraph, create 3 multiple-choice questions with 4 options each.\n"
        #     "3. Mark the correct answer for each question with an asterisk (*).\n"
        #     "Format your response with clear section headers for the content and questions."
        # )

        prompt = COMBINED_GENERATION_PROMPT.format(topic=topic)
        
        # Call WatsonX LLM with the prompt
        response = await self.llm.ainvoke(prompt)
        
        # Parse the response to extract content and questions
        content, questions = self._parse_response(response)
        
        return {
            "content": content,
            "questions": questions,
            "topic": topic
        }
    
    def _parse_response(self, response: str) -> tuple[str, list[Question]]:
        """Parse the LLM response into content and questions."""
        # Split into content and questions sections
        parts = response.split("CONTENT:")
        if len(parts) > 1:
            parts = parts[1].split("QUESTIONS:")
        else:
            parts = response.split("QUESTIONS:")
            
        content = parts[0].strip() if len(parts) > 1 else ""
        questions_text = parts[1].strip() if len(parts) > 1 else response
        
        # Parse questions
        questions = []
        seen_questions = set()  # Track seen question texts to avoid duplicates
        
        # Pattern to match questions
        q_pattern = r'Q\d+:\s*(.*?)\s*\n\s*A\.\s*(.*?)\s*\n\s*B\.\s*(.*?)\s*\n\s*C\.\s*(.*?)\s*\n\s*D\.\s*(.*?)(?:\n|$)'
        
        for match in re.finditer(q_pattern, questions_text, re.DOTALL):
            question_text = match.group(1).strip()
            
            # Skip if we've seen this question already
            if question_text in seen_questions:
                continue
            seen_questions.add(question_text)
            
            # Get options and check which one is marked as correct
            options = []
            for i, opt_text in enumerate(match.groups()[1:5]):
                opt = opt_text.strip()
                is_correct = opt.endswith('*')
                if is_correct:
                    opt = opt[:-1].strip()  # Remove the asterisk
                options.append(Option(text=f"{chr(65+i)}. {opt}", is_correct=is_correct))
            
            questions.append(Question(question_text=f"Q{len(questions)+1}: {question_text}", options=options))
            
            # Stop after finding 3 questions
            if len(questions) >= 3:
                break
        
        return content, questions
