from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.interview import InterviewPrepRequest, InterviewPrepResponse
from src.services.interview_service import InterviewPrepService

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/prep", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    payload: InterviewPrepRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generates candidate fit score, skill gap analysis, and tailored interview questions."""
    try:
        service = InterviewPrepService(db)
        return await service.generate_interview_prep(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))