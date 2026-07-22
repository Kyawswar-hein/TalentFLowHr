from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.schemas.candidate import ExtractedCandidateProfile

class CandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_candidate_from_doc(self, document_id: str, profile: ExtractedCandidateProfile):
        query = text("""
            INSERT INTO public.candidates (document_id, full_name, email, phone, location, skills, years_of_experience, summary)
            VALUES (:document_id, :full_name, :email, :phone, :location, :skills, :years_of_experience, :summary)
            RETURNING id;
        """)
        
        result = await self.db.execute(query, {
            "document_id": document_id,
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "skills": profile.skills,  # Passed as list/ARRAY
            "years_of_experience": profile.years_of_experience,
            "summary": profile.summary
        })
        await self.db.commit()
        return result.scalar_one()