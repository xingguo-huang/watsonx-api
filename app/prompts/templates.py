# Prompt template for combined content and quiz generation
COMBINED_GENERATION_PROMPT = """
Generate educational content about the topic: {topic}.

First, write a well-structured paragraph of approximately 100 words that explains 
key concepts about the topic in a clear, informative way suitable for beginners.

Then, create EXACTLY THREE multiple-choice questions based only on the information 
in your paragraph. Each question should have exactly four options (A, B, C, D), 
with exactly one correct answer marked with an asterisk (*).

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

CONTENT:
[Your educational paragraph here]

QUESTIONS:
Q1: [Question text]
A. [Option A]
B. [Option B]*
C. [Option C]
D. [Option D]

Q2: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]*
D. [Option D]

Q3: [Question text]
A. [Option A]*
B. [Option B]
C. [Option C]
D. [Option D]
"""

# filepath: /Users/xingguohuang/Downloads/watsonx-api/app/prompts/templates.py
LESSON_PLAN_PROMPT = """
You are an expert instructional designer specializing in {grade_level} education.

INPUTS:
1. Core Parameters:
   - Topic: {topic}
   - Duration: {duration} minutes total
   - Grade Level: {grade_level}

2. Teaching Approach:
   - Selected Teaching Style(s): {style}
   
   * Understanding Teaching Styles:
     - Expert: A teacher-centered approach where teachers hold knowledge and expertise, focusing on sharing knowledge and providing direct feedback.
     - Formal Authority: A teacher-centered approach focused on lecturing in a structured environment, ideal for delivering large amounts of information efficiently.
     - Personal Model: A teacher-centered approach using real-life examples with direct observation, where teacher acts as a coach/mentor.
     - Facilitator: A student-centered approach focused on guiding critical thinking through activities, emphasizing teacher-student interactions.
     - Delegator: A student-centered approach where teacher serves as an observer while students work independently or in groups.

TASK:
1) Create a detailed lesson plan that:
   - Is appropriate for {grade_level} students
   - Covers the topic "{topic}" thoroughly
   - Can be completed in {duration} minutes
   - Uses the "{style}" teaching style
   - Includes 3-5 clear learning objectives
   - Breaks down the lesson into logical phases
   - Provides detailed descriptions of each phase's activities

2) Create 3 multiple-choice assessment questions that:
   - Test understanding of the lesson content
   - Have 4 options each (A, B, C, D)
   - Clearly mark the correct answer with an asterisk (*)

RESPONSE FORMAT:
Your response must be PURE JSON with no additional text before or after. Follow the FORMAT exactly as follows:

{{
  "lesson_plan": {{
    "objectives": [
      "Objective 1",
      "Objective 2",
      "Objective 3"
    ],
    "outline": [
      {{
        "phase": "Introduction",
        "duration": "10 minutes",
        "purpose": "Engage students with the topic",
        "description": "Detailed description of activities and teaching approach"
      }},
      {{
        "phase": "Second Phase Name",
        "duration": "15 minutes",
        "purpose": "Purpose of this phase",
        "description": "Detailed description"
      }}
    ]
  }},
  "questions": [
    {{
      "question": "Question 1 text?",
      "options": ["Option A", "Option B*", "Option C", "Option D"]
    }},
    {{
      "question": "Question 2 text?",
      "options": ["Option A", "Option B", "Option C*", "Option D"]
    }},
    {{
      "question": "Question 3 text?",
      "options": ["Option A*", "Option B", "Option C", "Option D"]
    }}
  ]
}}

CRITICALLY IMPORTANT RULES:
1. Provide ONLY valid JSON in your response
2. Do NOT include ANY explanatory text or comments
3. Do NOT use markdown formatting or code blocks
4. Use DOUBLE QUOTES for all strings (not single quotes)
5. Do NOT use trailing commas (like "item",])
6. Properly escape any quotes or special characters in strings
7. Make sure all keys and values are properly quoted
8. The "questions" array MUST contain EXACTLY 3 questions - THIS IS MANDATORY
"""