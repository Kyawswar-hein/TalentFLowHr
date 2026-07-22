from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedCandidateProfile(BaseModel):
    full_name: str = Field(description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Primary email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="City/Country or current location")
    skills: List[str] = Field(default_factory=list, description="Key technical and soft skills")
    years_of_experience: Optional[float] = Field(default=0.0, description="Estimated total years of professional experience")
    summary: Optional[str] = Field(default=None, description="2-3 sentence executive summary of candidate")