from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.schemas.document import DocumentChunkCreate, DocumentChunkResponse, DocumentSearchQuery
from src.services.rag import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/ingest", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def ingest_single_document_chunk(
    chunk: DocumentChunkCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests a single text chunk, computes its 768-dim Gemini embedding, and saves it.
    """
    try:
        rag_service = RAGService(db)
        return await rag_service.ingest_single_chunk(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )

@router.post("/ingest/batch", response_model=list[DocumentChunkResponse], status_code=status.HTTP_201_CREATED)
async def ingest_batch_document_chunks(
    chunks: list[DocumentChunkCreate], 
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests multiple text chunks in a batch operation to minimize network roundtrips.
    """
    try:
        rag_service = RAGService(db)
        return await rag_service.ingest_chunks_batch(chunks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {str(e)}"
        )

@router.post("/search", status_code=status.HTTP_200_OK)
async def search_similar_chunks(
    query: DocumentSearchQuery, 
    db: AsyncSession = Depends(get_db)
):
    """
    Performs an async vector similarity search across document chunks based on language routing.
    """
    try:
        rag_service = RAGService(db)
        return await rag_service.retrieve_relevant_context(query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )