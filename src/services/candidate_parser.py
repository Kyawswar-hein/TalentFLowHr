import json
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_ollama import OllamaLLM

logger = logging.getLogger("uvicorn")


# ------------------------------------------------------------------
# Pydantic Output Schema
# ------------------------------------------------------------------
class ExtractedCandidateProfile(BaseModel):
    full_name: Optional[str] = Field(
        default=None, 
        description="The candidate's real personal full name."
    )
    email: Optional[str] = Field(
        default=None, 
        description="The candidate's primary email address."
    )
    phone: Optional[str] = Field(
        default=None, 
        description="The candidate's contact phone number."
    )
    target_role: str = Field(
        default="Software Engineer", 
        description="Standardized target technical role."
    )
    years_of_experience: float = Field(
        default=0.0, 
        description="Total estimated years of relevant professional experience."
    )
    skills: List[str] = Field(
        default_factory=list, 
        description="Key technical skills, languages, frameworks, and tools."
    )
    education: List[str] = Field(
        default_factory=list, 
        description="Degrees, universities, or academic qualifications."
    )


# ------------------------------------------------------------------
# Fallback Keyword Logic for Target Role Standardization
# ------------------------------------------------------------------
def refine_target_role_fallback(skills: List[str], raw_text: str, current_role: str) -> str:
    """Python fallback rules if LLM returns a generic or inaccurate role."""
    text_lower = (raw_text + " " + " ".join(skills)).lower()

    if any(k in text_lower for k in ["pytorch", "tensorflow", "machine learning", "computer vision", "llm", "langchain"]):
        return "AI / Machine Learning Engineer"
    elif any(k in text_lower for k in ["docker", "kubernetes", "aws", "ci/cd", "devops"]):
        return "DevOps Engineer"
    elif any(k in text_lower for k in ["react", "vue", "angular", "tailwind", "next.js"]) and not any(k in text_lower for k in ["spring", "fastapi", "django"]):
        return "Frontend Engineer"
    elif any(k in text_lower for k in ["spring boot", "fastapi", "laravel", "express", "backend"]):
        if any(k in text_lower for k in ["react", "vue", "frontend", "mern"]):
            return "Full-Stack Engineer"
        return "Backend Engineer"
    
    return current_role if current_role and current_role != "Software Engineer" else "Full-Stack Engineer"


# ------------------------------------------------------------------
# Main Extractor Service
# ------------------------------------------------------------------
async def extract_candidate_info(raw_text: str) -> ExtractedCandidateProfile:
    """
    Uses local Llama 3.1 via Ollama to extract structured candidate profile 
    fields from resume text using Pydantic JSON schema enforcement.
    """
    if not raw_text or not raw_text.strip():
        return ExtractedCandidateProfile()

    # Initialize local Ollama model
    llm = OllamaLLM(model="llama3.1:latest", format="json", temperature=0.0)

    prompt = f"""
You are an expert HR recruitment parser. Analyze the following resume text and extract the candidate's structured profile information as a JSON object.

### FIELD-BY-FIELD EXTRACTION RULES:

1. 'full_name':
   - Extract ONLY the candidate's real personal full name (e.g., "Kyaw Swar Hein").
   - DO NOT include company names, client names, or project tags (e.g., ignore "COOSY", "DIR-ACE", "DAT", "Ltd").
   - DO NOT include file metadata, status text, or section headers (e.g., ignore "CV", "Resume", "Unknown Candidate").
   - If no personal name is found, set as null.

2. 'email':
   - Extract the primary email address. Return null if not present.

3. 'phone':
   - Extract phone number. Return null if not present.

4. 'target_role':
   - Infer standardized role based on skills and experience:
     * Java / Spring / FastAPI / Backend -> "Backend Engineer"
     * React / Vue / Frontend -> "Frontend Engineer"
     * Python / ML / PyTorch / Computer Vision -> "AI / Machine Learning Engineer"
     * Docker / Kubernetes / AWS -> "DevOps Engineer"
     * MERN / Full-Stack / Spring + Frontend -> "Full-Stack Engineer"

5. 'years_of_experience':
   - Estimate total years of professional/internship work experience as a float (e.g., 1.5, 3.0, 5.0).
   - If candidate is a fresh graduate or student, set as 0.5 or 1.0.

6. 'skills':
   - Extract a list of technical skills, programming languages, databases, and tools mentioned (e.g., ["Java", "Spring Boot", "Python", "FastAPI", "PostgreSQL", "Tailwind CSS"]).

7. 'education':
   - Extract degrees, majors, and institutions (e.g., ["B.E. Information Technology - MIIT"]).

Return ONLY valid JSON matching this structure:
{{
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "target_role": "string",
  "years_of_experience": 0.0,
  "skills": ["string"],
  "education": ["string"]
}}

RESUME TEXT:
{raw_text[:4000]}
"""

    try:
        response_text = await llm.ainvoke(prompt)
        parsed_json = json.loads(response_text)
        
        # Instantiate Pydantic model
        profile = ExtractedCandidateProfile(**parsed_json)

        # Apply Python fallback rules for target role refinement
        profile.target_role = refine_target_role_fallback(profile.skills, raw_text, profile.target_role)

        # Post-clean full_name if company tags sneaked through
        if profile.full_name:
            profile.full_name = re.sub(r'(?i)\s*[-_]\s*coosy.*$', '', profile.full_name).strip()

        return profile

    except Exception as e:
        logger.error(f"Error parsing candidate profile with Ollama llama3.1: {e}")
        return ExtractedCandidateProfile()