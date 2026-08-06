"""
Interview Agent - Orchestrates multi-round interview using Groq API
"""

from groq import Groq
from prompts import get_round_prompt
from typing import List, Dict, Optional
import json
import re


def infer_difficulty(background: str) -> str:
    """Infer difficulty level from the candidate's background text."""
    if not background:
        return "intermediate"
    
    bg_lower = background.lower()
    
    beginner_keywords = [
        "fresher", "student", "graduate", "intern", "college",
        "university", "0 year", "no experience", "entry level",
        "beginner", "learning", "new to", "btech", "b.tech",
        "mca", "bca", "mba", "pursuing", "final year", "passout",
        "pass out", "12th", "school"
    ]
    
    for kw in beginner_keywords:
        if kw in bg_lower:
            return "beginner"
    
    # Check for low experience (1-3 years)
    exp_match = re.search(r'(\d+)\s*(?:year|yr)', bg_lower)
    if exp_match:
        years = int(exp_match.group(1))
        if years <= 1:
            return "beginner"
        elif years <= 3:
            return "intermediate"
        else:
            return "advanced"
    
    return "intermediate"


DIFFICULTY_INSTRUCTIONS = {
    "beginner": (
        "\n\nIMPORTANT - DIFFICULTY LEVEL: EASY/MODERATE\n"
        "The candidate is a fresher or student with little to no professional experience.\n"
        "- Ask easy to moderate difficulty questions\n"
        "- Start with fundamentals and basics\n"
        "- Be encouraging and provide hints when they struggle\n"
        "- Focus on conceptual understanding, not advanced system design\n"
        "- Ask about academic projects, internships, or personal projects\n"
        "- Keep questions practical and relatable for a beginner\n"
    ),
    "intermediate": (
        "\n\nIMPORTANT - DIFFICULTY LEVEL: MODERATE\n"
        "The candidate has some professional experience (1-3 years).\n"
        "- Ask moderate difficulty questions\n"
        "- Probe deeper on fundamentals and practical experience\n"
        "- Ask about real projects and challenges faced\n"
        "- Include some design/architecture questions at a basic level\n"
    ),
    "advanced": (
        "\n\nIMPORTANT - DIFFICULTY LEVEL: HARD/CHALLENGING\n"
        "The candidate is experienced (4+ years) in their field.\n"
        "- Ask challenging, in-depth questions\n"
        "- Expect detailed, nuanced answers with trade-offs\n"
        "- Include system design, architecture, and leadership questions\n"
        "- Probe on scale, performance, and real-world complexities\n"
        "- Challenge their assumptions and ask for alternatives\n"
    ),
}

# Map the UI role names to prompts.py keys
ROLE_TO_PROMPT_KEY = {
    "SDE": "SDE",
    "Data Scientist": "Data Scientist",
    "PM": "Product Manager",
}


class InterviewAgent:
    def __init__(self, api_key: str, role: str, resume_context: str = "", background: str = ""):
        """Initialize the interview agent"""
        self.client = Groq(api_key=api_key)
        self.role = role
        self.prompt_role = ROLE_TO_PROMPT_KEY.get(role, role)
        self.resume_context = resume_context
        self.background = background
        self.difficulty = infer_difficulty(background)
        self.interview_history = []
        self.model = "llama-3.1-8b-instant"  # Fast model with higher TPM limit
        
    def add_question_to_history(self, round_name: str, question: str):
        """Add a question to the interview history"""
        round_data = self._get_or_create_round(round_name)
        round_data["conversation"].append({
            "type": "question",
            "content": question
        })
        round_data["questions_asked"] += 1

    def add_answer_to_history(self, round_name: str, answer: str, evaluation: str = ""):
        """Add an answer and its evaluation to the interview history"""
        round_data = self._get_or_create_round(round_name)
        round_data["conversation"].append({
            "type": "answer",
            "content": answer
        })
        q_num = len(round_data["answers"]) + 1
        round_data["answers"].append({
            "question_num": q_num,
            "answer": answer,
            "evaluation": evaluation
        })

    def _get_or_create_round(self, round_name: str) -> Dict:
        """Get existing round data or create a new one"""
        for r in self.interview_history:
            if r["round"] == round_name:
                return r
        round_data = {
            "round": round_name,
            "questions_asked": 0,
            "answers": [],
            "conversation": []
        }
        self.interview_history.append(round_data)
        return round_data
        
    def evaluate_answer(self, question: str, answer: str, round_name: str) -> Dict:
        """Evaluate a single answer"""
        
        evaluator_prompt = get_round_prompt(self.prompt_role, round_name, "evaluator")
        
        eval_message = f"""
Question: {question}
Candidate Answer: {answer}

Evaluate this answer briefly (3-4 sentences). Mention strengths and one area to improve.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": evaluator_prompt},
                    {"role": "user", "content": eval_message}
                ]
            )
            
            evaluation = response.choices[0].message.content
            return {"answer": answer, "evaluation": evaluation}
        except Exception as e:
            return {"error": str(e)}
    
    def get_final_feedback(self) -> str:
        """Generate comprehensive feedback after all rounds"""
        
        coach_prompt = f"""You are a supportive career coach providing feedback to a {self.role} candidate after their interview rounds.

Based on the interview performance across all rounds, provide:
1. **Overall Assessment** (2-3 sentences)
2. **Top 3 Strengths** (specific competencies)
3. **Top 3 Areas for Improvement** (with concrete examples)
4. **Personalized Learning Plan** (3-5 specific actions)
5. **Confidence Level for Role** (1-10 with reasoning)
6. **Next Steps** (what to do before next interview)

Be encouraging, specific, and actionable. Focus on growth."""
        
        # Build a COMPACT summary instead of full JSON to stay under token limits
        summary_lines = []
        for rd in self.interview_history:
            summary_lines.append(f"\n--- Round: {rd['round']} ---")
            for item in rd.get("conversation", []):
                prefix = "Q" if item["type"] == "question" else "A"
                # Truncate long entries
                content = item["content"][:300]
                summary_lines.append(f"{prefix}: {content}")
        
        compact_summary = "\n".join(summary_lines)
        # Hard cap at 4000 chars to stay safe
        if len(compact_summary) > 4000:
            compact_summary = compact_summary[:4000] + "\n...(truncated)"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {"role": "system", "content": coach_prompt},
                    {"role": "user", "content": f"Interview transcript:\n{compact_summary}"}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating feedback: {e}"
    
    def get_question(self, round_name: str, question_num: int, previous_answer: Optional[str] = None) -> str:
        """Get the next question in a round"""
        
        system_prompt = get_round_prompt(self.prompt_role, round_name, "system")
        
        # Add difficulty instruction
        system_prompt += DIFFICULTY_INSTRUCTIONS.get(self.difficulty, "")
        
        # Add resume context if available
        if self.resume_context:
            system_prompt += f"\n\n{self.resume_context}"
        
        # Add background context
        if self.background:
            system_prompt += f"\n\nCandidate background: {self.background}"
        
        if question_num == 1:
            user_message = "Start the interview with your first question. Ask only ONE clear question."
        else:
            if previous_answer:
                user_message = f"The candidate answered: '{previous_answer}'\n\nAsk the next follow-up or new question. Ask only ONE clear question."
            else:
                user_message = "Ask the next question. Ask only ONE clear question."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting question: {e}"


class InterviewOrchestrator:
    """Orchestrates the complete interview process across multiple rounds"""
    
    def __init__(self, api_key: str, role: str, resume_context: str = "", background: str = ""):
        self.api_key = api_key
        self.role = role
        self.resume_context = resume_context
        self.background = background
        self.rounds = self._get_rounds_for_role()
        self.agent = InterviewAgent(api_key, role, resume_context, background)
        
    def _get_rounds_for_role(self) -> List[str]:
        """Get the rounds for a specific role"""
        rounds_map = {
            "SDE": ["Technical", "HR", "Problem-Solving"],
            "Data Scientist": ["Technical", "HR", "Case Study"],
            "PM": ["Product Sense", "HR", "Analytics & Strategy"]
        }
        return rounds_map.get(self.role, [])
    
    def get_all_rounds(self) -> List[str]:
        """Return all rounds for this role"""
        return self.rounds
    
    def start_round(self, round_name: str) -> str:
        """Start a specific round and get first question"""
        question = self.agent.get_question(round_name, 1)
        self.agent.add_question_to_history(round_name, question)
        return question
    
    def answer_question(self, round_name: str, question: str, answer: str, question_num: int) -> str:
        """Process candidate answer and get next question"""
        # Evaluate the answer
        eval_result = self.agent.evaluate_answer(question, answer, round_name)
        evaluation = eval_result.get("evaluation", "")
        
        # Save answer and evaluation to history
        self.agent.add_answer_to_history(round_name, answer, evaluation)
        
        # Get next question
        next_question = self.agent.get_question(round_name, question_num + 2, answer)
        
        # Save next question to history
        self.agent.add_question_to_history(round_name, next_question)
        
        return next_question

    def submit_final_answer(self, round_name: str, question: str, answer: str) -> None:
        """Process and evaluate the final answer of the round"""
        eval_result = self.agent.evaluate_answer(question, answer, round_name)
        evaluation = eval_result.get("evaluation", "")
        self.agent.add_answer_to_history(round_name, answer, evaluation)
    
    def finalize_round(self, round_name: str) -> str:
        """Finalize a round and provide feedback"""
        return self.agent.get_final_feedback()
