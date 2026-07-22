from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.database import get_db

router = APIRouter(prefix="/candidates", tags=["candidates"])

class CandidateResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    created_at: Optional[str] = None

@router.get("", response_model=List[CandidateResponse])
async def list_candidates(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Fetches structured candidate profiles for the UI grid/table."""
    query = text("""
        SELECT id, full_name, email, target_role, experience_level, created_at::text
        FROM public.candidates
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset;
    """)
    result = await db.execute(query, {"limit": limit, "offset": offset})
    rows = result.mappings().fetchall()
    return [dict(row) for row in rows]