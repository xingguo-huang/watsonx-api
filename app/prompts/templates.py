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
