# src/api/v1/endpoints/agent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db  # Adjust to your database dependency path
from src.services.rag import RAGService
from src.schemas.document import DocumentSearchQuery # Or your dedicated agent query schema

router = APIRouter()

@router.post("/query")
async def query_agent(payload: DocumentSearchQuery, db: AsyncSession = Depends(get_db)):
    try:
        rag_service = RAGService(db)
        # Call the orchestrator method we added to RAGService
        response = await rag_service.query_agent(
            user_query=payload.query, 
            top_k=payload.top_k
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database retrieval failed: {str(e)}"
        )