import os
import re
import logging
from typing import Union, Any, List, Dict
from pypdf import PdfReader
from docx import Document as DocxReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.document import DocumentRepository
from src.services.embedding import embedding_service
from src.schemas.document import DocumentChunkCreate, DocumentSearchQuery, DocumentChunkResponse

logger = logging.getLogger("uvicorn")


class RAGService:
    def __init__(self, db: AsyncSession):
        self.repo = DocumentRepository(db)

    # ------------------------------------------------------------------
    # 1. Text Extraction Utilities
    # ------------------------------------------------------------------
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extracts plain text from PDF, DOCX, or TXT files cleanly with normalized spacing."""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    # Fix missing spaces between lowercase and uppercase camel bounds (e.g. ArchitectedARole -> Architected A Role)
                    cleaned_page = re.sub(r'([a-z])([A-Z])', r'\1 \2', extracted)
                    # Insert space between words separated by non-standard word boundaries
                    cleaned_page = re.sub(r'([a-zA-Z0-9])\(', r'\1 (', cleaned_page)
                    text += cleaned_page + "\n"
        elif ext in [".docx", ".doc"]:
            doc = DocxReader(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        # Clean redundant spaces and tabs while retaining clean sentence boundaries
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
        """Splits raw text into semantic chunks."""
        if not text:
            return []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        return splitter.split_text(text)

    # ------------------------------------------------------------------
    # 2. Chunk Ingestion Methods
    # ------------------------------------------------------------------
    async def ingest_single_chunk(self, chunk_in: DocumentChunkCreate) -> DocumentChunkResponse:
        """Computes embedding for a single chunk and persists to database."""
        vector = await embedding_service.get_embedding(chunk_in.content, is_query=False)
        db_chunk = await self.repo.create_chunk(chunk_in, vector)
        return DocumentChunkResponse.model_validate(db_chunk)

    async def ingest_chunks_batch(self, chunks_in: list[DocumentChunkCreate]) -> list[DocumentChunkResponse]:
        """
        Batch ingests multiple text chunks using Ollama batch embeddings 
        and persists them into public.document_chunks.
        """
        if not chunks_in:
            return []
            
        texts = [chunk.content for chunk in chunks_in]
        vectors = await embedding_service.get_embeddings_batch(texts, is_query=False)
        db_chunks = await self.repo.create_chunks_batch(chunks_in, vectors)
        
        return [DocumentChunkResponse.model_validate(chunk) for chunk in db_chunks]

    # ------------------------------------------------------------------
    # 3. File Processing Pipeline
    # ------------------------------------------------------------------
    async def ingest_document_file(
        self, 
        document_id: str, 
        document_name: str, 
        file_path: str, 
        language: str = "en"
    ) -> list[DocumentChunkResponse]:
        """
        Extracts text from a file, chunks it, generates vector embeddings via Ollama,
        and saves all chunks to public.document_chunks.
        """
        raw_text = self.extract_text_from_file(file_path)
        if not raw_text:
            logger.warning(f"No text extracted from file: {file_path}")
            return []

        text_chunks = self.chunk_text(raw_text)
        
        chunks_to_create = [
            DocumentChunkCreate(
                document_id=document_id,
                document_name=document_name,
                content=chunk,
                chunk_index=idx,
                language=language
            )
            for idx, chunk in enumerate(text_chunks)
        ]

        logger.info(f"Generated {len(chunks_to_create)} chunks for document '{document_name}' ({document_id})")
        return await self.ingest_chunks_batch(chunks_to_create)

    # ------------------------------------------------------------------
    # 4. Search & Agent RAG Methods
    # ------------------------------------------------------------------
    async def query_agent(self, user_query: str, top_k: int = 3) -> dict:
        query_vector = await embedding_service.get_embedding(user_query, is_query=True)
        results = await self.repo.search_similar_chunks(
            query_embedding=query_vector,
            language=None, 
            top_k=top_k
        )
        
        relevant_chunks = [chunk for chunk, distance in results if distance <= 0.8]
        
        if not relevant_chunks:
            return {
                "query": user_query,
                "answer": "I could not find any relevant candidate records to answer your question.",
                "sources": []
            }
            
        context_str = "\n\n".join([c.content for c in relevant_chunks])
        
        from src.services.gemini_service import generate_answer
        answer = await generate_answer(user_query=user_query, context=context_str)
        
        return {
            "query": user_query,
            "answer": answer,
            "sources": [
                {"id": c.id, "document_name": c.document_name, "content": c.content} 
                for c in relevant_chunks
            ]
        }

    async def retrieve_relevant_context(
        self, 
        search_query: Union[DocumentSearchQuery, dict, str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top matching vector chunks and deduplicates by document 
        so each candidate/document appears only once.
        """
        query_text = ""
        lang = None
        limit_k = top_k

        if isinstance(search_query, str):
            query_text = search_query
        elif isinstance(search_query, dict):
            query_text = search_query.get("query", "")
            lang = search_query.get("language", None)
            limit_k = search_query.get("top_k", top_k)
        else:
            query_text = getattr(search_query, "query", "")
            lang = getattr(search_query, "language", None)
            limit_k = getattr(search_query, "top_k", top_k)

        query_vector = await embedding_service.get_embedding(query_text, is_query=True)
        
        # Fetch extra chunks initially so we still have enough matches after deduplication
        raw_results = await self.repo.search_similar_chunks(
            query_embedding=query_vector,
            language=lang,
            top_k=limit_k * 4
        )
        
        formatted_results = []
        seen_documents = set()

        for chunk, distance in raw_results:
            # Group / Deduplicate by document_name (or document_id)
            doc_identifier = chunk.document_name or chunk.document_id
            
            if doc_identifier not in seen_documents:
                seen_documents.add(doc_identifier)
                formatted_results.append({
                    "id": chunk.id,
                    "document_name": chunk.document_name,
                    "language": chunk.language,
                    "content": chunk.content,
                    "extra_metadata": chunk.extra_metadata,
                    "distance_score": distance
                })
            
            # Stop once we have reached the requested top_k unique candidates
            if len(formatted_results) >= limit_k:
                break
            
        return formatted_results