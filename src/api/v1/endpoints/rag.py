from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.agentic_rag import build_agent_graph

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search")
async def search_resume_chunks(
    payload: RAGSearchRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Executes stateful Agentic RAG search via LangGraph."""
    try:
        graph = build_agent_graph(db)

        initial_state = {
            "query": payload.query,
            "intent": "",
            "vector_results": [],
            "final_response": ""
        }

        final_output = await graph.ainvoke(initial_state)

        return {
            "query": payload.query,
            "intent": final_output.get("intent", "vector_search"),
            "answer": final_output.get("final_response", ""),
            "results": final_output.get("vector_results", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))