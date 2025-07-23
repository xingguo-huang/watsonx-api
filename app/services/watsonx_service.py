from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from langchain_ibm import WatsonxLLM
from ibm_watsonx_ai import Credentials
import json
from typing import List, Dict, Any, Tuple
import re

from app.core.settings import settings
from app.schemas.generation import Question, Option, Phase, LessonPlan
from app.prompts.templates import COMBINED_GENERATION_PROMPT, LESSON_PLAN_PROMPT, WEB_ENHANCED_GENERATION_PROMPT
from app.services.google_search_service import GoogleSearchService


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

        # Initialize Google Search service
        self.google_search = GoogleSearchService()

    async def generate_content_and_quiz(self, topic: str, use_web_context: bool = False) -> Dict[str, Any]:
        """Generate both content and quiz questions based on the given topic"""
        
        web_context = ""
        if use_web_context:
            try:
                print(f"Fetching web context for topic: {topic}")
                web_context = self.google_search.search(topic)
                print(f"Found {web_context.count('Source')} sources for web context")
            except Exception as e:
                print(f"Error fetching web context: {str(e)}")
                # Continue without web context if there's an error
        
        # Choose appropriate prompt based on whether we have web context
        if use_web_context and web_context:
            prompt = WEB_ENHANCED_GENERATION_PROMPT.format(
                topic=topic,
                web_context=web_context
            )
        else:
            prompt = COMBINED_GENERATION_PROMPT.format(topic=topic)
        
        # Call WatsonX LLM with the prompt
        response = await self.llm.ainvoke(prompt)
        
        # Parse the response to extract content and questions
        content, questions = self._parse_response(response)
        
        return {
            "content": content,
            "questions": questions,
            "topic": topic,
            "used_web_context": use_web_context and bool(web_context)
        }
    
    def _parse_response(self, response: str) -> Tuple[str, List[Question]]:
        """Parse the LLM response with robust handling of malformed responses."""
        content = ""
        questions = []
        
        # STEP 1: Try normal structured parsing first
        if "CONTENT:" in response and "QUESTIONS:" in response:
            content = response.split("CONTENT:")[1].split("QUESTIONS:")[0].strip()
            questions_text = response.split("QUESTIONS:")[1].strip()
            questions = self._extract_questions_from_text(questions_text)
        
        # STEP 2: If we have content but no questions, check if questions are embedded in content
        elif "CONTENT:" in response:
            raw_content = response.split("CONTENT:")[1].strip()
            content, embedded_questions = self._extract_embedded_questions(raw_content)
            questions = embedded_questions
            
        # STEP 3: If only questions section exists
        elif "QUESTIONS:" in response:
            questions_text = response.split("QUESTIONS:")[1].strip()
            questions = self._extract_questions_from_text(questions_text)
        
        # STEP 4: Unstructured response - try to parse the whole thing
        else:
            content, embedded_questions = self._extract_embedded_questions(response)
            questions = embedded_questions
        
        # Ensure we have at most 3 questions
        if len(questions) > 3:
            questions = questions[:3]
            
        return content, questions

    def _extract_questions_from_text(self, text: str) -> List[Question]:
        """Extract properly formatted questions from text."""
        questions = []
        seen_questions = set()
        
        # Standard pattern for Q1, Q2, etc. format
        q_pattern = r'Q\d+:\s*(.*?)\s*\n\s*A\.\s*(.*?)\s*\n\s*B\.\s*(.*?)\s*\n\s*C\.\s*(.*?)\s*\n\s*D\.\s*(.*?)(?:\n|$)'
        for match in re.finditer(q_pattern, text, re.DOTALL):
            question = self._create_question_from_match(match, seen_questions)
            if question:
                questions.append(question)
                if len(questions) >= 3:
                    break
                    
        return questions

    def _extract_embedded_questions(self, text: str) -> Tuple[str, List[Question]]:
        """Extract questions that might be embedded within content text."""
        cleaned_content = text
        questions = []
        seen_questions = set()
        
        # Find question-like patterns in the content
        # Pattern 1: Q1, Q2, etc. format
        q_pattern = r'Q\d+:\s*(.*?)\s*\n\s*A\.\s*(.*?)\s*\n\s*B\.\s*(.*?)\s*\n\s*C\.\s*(.*?)\s*\n\s*D\.\s*(.*?)(?:\n|$)'
        for match in re.finditer(q_pattern, text, re.DOTALL):
            question = self._create_question_from_match(match, seen_questions)
            if question:
                questions.append(question)
                # Remove this question from content
                full_match = match.group(0)
                cleaned_content = cleaned_content.replace(full_match, "")
        
        # Pattern 2: Options without Q prefix (A. B. C. D. format) - common in malformed outputs
        if len(questions) == 0:
            option_pattern = r'(?:\n|^)([A-D])\.\s*(.*?)\s*\n\s*([A-D])\.\s*(.*?)\s*\n\s*([A-D])\.\s*(.*?)\s*\n\s*([A-D])\.\s*(.*?)(?:\n|$)'
            option_matches = list(re.finditer(option_pattern, text, re.DOTALL))
            
            # If we find option patterns, try to group them into questions (3 sets of 4 options)
            current_q_text = "Question about the topic"
            
            for i, match in enumerate(option_matches):
                # Extract all option groups
                options_data = []
                correct_found = False
                
                # Process the 4 options (letters and texts)
                for j in range(0, 8, 2):
                    if j+1 < len(match.groups()):
                        letter = match.group(j+1)
                        option_text = match.group(j+2).strip()
                        
                        # Check for asterisk anywhere
                        is_correct = "*" in option_text
                        if is_correct:
                            correct_found = True
                            option_text = option_text.replace("*", "").strip()
                        
                        options_data.append((letter, option_text, is_correct))
                
                # If we found 4 options, create a question
                if len(options_data) == 4:
                    # Try to find a question text before this set of options
                    context_before = text[:match.start()].strip()
                    last_sentence = re.search(r'([^.!?]*[.!?])(?:\s|$)[^A-D]?$', context_before)
                    
                    if last_sentence:
                        current_q_text = last_sentence.group(1).strip()
                    
                    options = []
                    for letter, opt_text, is_correct in options_data:
                        options.append(Option(
                            text=f"{letter}. {opt_text}",
                            is_correct=is_correct
                        ))
                    
                    # Default to option A if no correct answer marked
                    if not correct_found and options:
                        options[0].is_correct = True
                        print(f"Warning: No correct option marked for extracted question. Defaulting to option A.")
                    
                    questions.append(Question(
                        question_text=f"Q{len(questions)+1}: {current_q_text}",
                        options=options
                    ))
                    
                    # Remove this question block from content
                    full_match = match.group(0)
                    cleaned_content = cleaned_content.replace(full_match, "")
                    
                    # Also remove the question text if we found it
                    if last_sentence:
                        cleaned_content = cleaned_content.replace(last_sentence.group(1), "")
                    
                    if len(questions) >= 3:
                        break
    
        # Clean any remaining question-like patterns
        question_patterns = [
            r'(?:\n|^)Q\d+:.*?\n',
            r'(?:\n|^)[A-D]\.\s.*?\n', 
            r'(?:\n|^)\*[A-D]\.\s.*?\n'
        ]
        
        for pattern in question_patterns:
            cleaned_content = re.sub(pattern, '\n', cleaned_content, flags=re.MULTILINE)
        
        # Final cleanup
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)  # Remove excessive newlines
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content, questions

    def _create_question_from_match(self, match, seen_questions):
        """Create a Question object from a regex match object."""
        question_text = match.group(1).strip()
        
        # Skip duplicate questions
        if question_text in seen_questions:
            return None
        
        seen_questions.add(question_text)
        
        raw_options = match.groups()[1:5]
        options = []
        correct_found = False
        
        for i, opt_text in enumerate(raw_options):
            text = opt_text.strip()
            is_correct = False
            
            # Detect * anywhere in the text
            if "*" in text:
                is_correct = True
                text = text.replace("*", "").strip()
                correct_found = True
            
            options.append(Option(
                text=f"{chr(65+i)}. {text}",
                is_correct=is_correct
            ))
        
        # Fallback: If no correct option detected, just mark A as correct
        if not correct_found and options:
            options[0].is_correct = True
            print(f"Warning: No correct option marked for question '{question_text}'. Defaulting to option A.")
        
        return Question(
            question_text=f"Q{len(seen_questions)}: {question_text}",
            options=options
        )

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
