from typing import List, Optional
from pydantic import BaseModel, Field


class InterviewPrepRequest(BaseModel):
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: str
    job_description: str
    language: str = "en"  # "en" or "jp"


class InterviewQuestion(BaseModel):
    question_number: int
    category: str  # e.g., "Technical Depth", "Architecture", "Problem Solving", "Behavioral"
    question: str
    expected_answer: str
    key_evaluation_points: List[str]


class InterviewPrepResponse(BaseModel):
    candidate_name: str
    job_title: str
    fit_score: float = Field(..., description="Estimated candidate fit percentage 0-100%")
    executive_summary: str
    skill_gaps: List[str]
    matched_skills: List[str]
    questions: List[InterviewQuestion]