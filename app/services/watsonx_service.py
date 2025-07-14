from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from langchain_ibm import WatsonxLLM
from ibm_watsonx_ai import Credentials
import json
from typing import List, Dict, Any, Tuple
import re

from app.core.settings import settings
from app.schemas.generation import Question, Option, Phase, LessonPlan
from app.prompts.templates import COMBINED_GENERATION_PROMPT, LESSON_PLAN_PROMPT


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

    async def generate_lesson_plan(self, 
                           topic: str, 
                           duration: int, 
                           grade_level: str, 
                           style: str) -> Dict[str, Any]:
        """Generate a lesson plan with quiz questions based on the given parameters"""
        
        try:
            # Create prompt with lesson plan parameters
            prompt = LESSON_PLAN_PROMPT.format(
                topic=topic,
                duration=duration,
                grade_level=grade_level,
                style=style
            )
            
            # Call WatsonX LLM with the prompt
            response = await self.llm.ainvoke(prompt)
            
            # Debug: Print first 500 chars of response to see what we're getting
            print(f"LLM Response preview: {response[:500]}")
            
            # Parse the JSON response
            lesson_plan, questions = self._parse_lesson_plan_response(response)
            
            return {
                "lesson_plan": lesson_plan,
                "questions": questions,
                "topic": topic
            }
        except Exception as e:
            # Add comprehensive error logging
            import traceback
            print(f"Error generating lesson plan: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _parse_lesson_plan_response(self, response: str) -> Tuple[LessonPlan, List[Question]]:
        """Parse the LLM response with enhanced error handling for malformed JSON."""
        try:
            # First attempt: Try to find JSON between triple backticks
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_content = json_match.group(1).strip()
            else:
                # Second attempt: Find JSON by braces
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_content = response[start:end]
                else:
                    json_content = response
        
            # Enhanced JSON cleanup for common syntax errors
            # Remove trailing commas before closing brackets (major cause of errors)
            json_content = re.sub(r',(\s*[\]}])', r'\1', json_content)
            
            # Fix missing quotes around property names
            json_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_content)
            
            # Fix single quotes to double quotes (careful with already escaped quotes)
            json_content = re.sub(r"(?<!\\)'([^']*?)(?<!\\)'", r'"\1"', json_content)
            
            # Print debugging info
            print(f"Cleaned JSON content (first 100 chars): {json_content[:100]}")
            
            # Try to parse the cleaned JSON
            data = json.loads(json_content)
            
            # Process the data as before...
            lesson_plan = LessonPlan(
                objectives=data["lesson_plan"]["objectives"],
                outline=[
                    Phase(
                        phase=phase["phase"],
                        duration=phase["duration"],
                        purpose=phase["purpose"],
                        description=phase["description"]
                    ) for phase in data["lesson_plan"]["outline"]
                ]
            )
            
            # Extract questions
            questions = []
            for q in data.get("questions", []):
                if "question" in q and "options" in q:
                    options_list = []
                    for i, opt in enumerate(q["options"]):
                        is_correct = "*" in str(opt)
                        text = str(opt).replace("*", "").strip()
                        options_list.append(Option(
                            text=f"{chr(65+i)}. {text}",
                            is_correct=is_correct
                        ))
                
                    questions.append(Question(
                        question_text=q["question"],
                        options=options_list
                    ))
        
            return lesson_plan, questions
        
        except Exception as e:
            # Fall back to regex-based extraction if JSON parsing fails
            return self._fallback_regex_parse(response, str(e))
    
    def _fallback_regex_parse(self, response: str, error_msg: str) -> Tuple[LessonPlan, List[Question]]:
        """Extract lesson plan data using regex when JSON parsing fails completely."""
        try:
            # Extract objectives with regex
            objectives = []
            obj_pattern = r'"objectives"\s*:\s*\[(.*?)\]'
            obj_match = re.search(obj_pattern, response, re.DOTALL)
            if obj_match:
                obj_text = obj_match.group(1)
                for m in re.finditer(r'"([^"]*)"', obj_text):
                    objectives.append(m.group(1))
        
            # Extract phases with regex
            phases = []
            phase_pattern = r'"phase"\s*:\s*"([^"]*)"\s*,\s*"duration"\s*:\s*"([^"]*)"\s*,\s*"purpose"\s*:\s*"([^"]*)"\s*,\s*"description"\s*:\s*"([^"]*)"'
            for m in re.finditer(phase_pattern, response, re.DOTALL):
                phases.append(Phase(
                    phase=m.group(1).strip(),
                    duration=m.group(2).strip(),
                    purpose=m.group(3).strip(),
                    description=m.group(4).strip()
                ))
        
            # If we found valid data, return it
            if objectives and phases:
                return LessonPlan(objectives=objectives, outline=phases), []
        except:
            pass
    
        # If all parsing attempts failed, return error information
        return LessonPlan(
            objectives=["Unable to generate lesson plan due to technical error"],
            outline=[
                Phase(
                    phase="Error",
                    duration="N/A",
                    purpose="The lesson plan could not be generated",
                    description=f"Error parsing response: {error_msg}"
                )
            ]
        ), []
