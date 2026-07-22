import hashlib
import os
import re
import uuid
import logging
import mimetypes
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.database import get_db, AsyncSessionLocal 
from src.services.rag import RAGService
from src.services.candidate_parser import extract_candidate_info

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "./uploaded_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class HashCheckRequest(BaseModel):
    file_hashes: List[str]


class HashCheckResponse(BaseModel):
    existing_hashes: List[str]


def fallback_filename_cleaner(filename: str) -> str:
    """Fallback if LLM cannot find a name in raw text."""
    base = os.path.splitext(filename)[0]
    base = re.sub(r'(?i)\s*[-_]\s*(coosy|cv|resume|draft|final).*$', '', base)
    base = re.sub(r'[\(\[\{]\d+[\)\]\}]', '', base)
    base = re.sub(r'[-_]+', ' ', base).strip()
    return base.title() if base else "Candidate"


async def process_document_vectorization(doc_id: str, original_name: str, file_path: str):
    """
    Background worker:
    1. Chunks & creates embeddings in public.document_chunks
    2. Uses Ollama llama3.1 to extract candidate details -> public.candidates
    3. Updates public.documents with the created candidate_id
    """
    async with AsyncSessionLocal() as session:
        try:
            # 1. Chunk and Vectorize Document for RAG Search
            rag_service = RAGService(session)
            await rag_service.ingest_document_file(
                document_id=str(doc_id),
                document_name=original_name,
                file_path=file_path
            )

            # 2. Extract Text for LLM Candidate Parsing
            raw_text = rag_service.extract_text_from_file(file_path)
            if raw_text:
                candidate_profile = await extract_candidate_info(raw_text)

                llm_name = candidate_profile.full_name if candidate_profile else None
                invalid_names = ["unknown candidate", "unknown", "n/a", "none", "", "null"]

                if not llm_name or llm_name.strip().lower() in invalid_names:
                    parsed_name = fallback_filename_cleaner(original_name)
                else:
                    parsed_name = re.sub(r'(?i)\s*[-_]\s*coosy.*$', '', llm_name).strip()

                target_role = (
                    candidate_profile.target_role 
                    if candidate_profile and getattr(candidate_profile, 'target_role', None) 
                    else "Software Engineer"
                )
                
                exp = getattr(candidate_profile, 'years_of_experience', 0.0) if candidate_profile else 0.0
                exp = exp or 0.0
                if exp < 2.0:
                    experience_level = "Junior"
                elif exp <= 5.0:
                    experience_level = "Mid-Level"
                elif exp <= 8.0:
                    experience_level = "Mid-Level"
                elif exp < 8.0:
                    experience_level = "Senior"
                else:
                    experience_level = "Lead / Principal"



                candidate_email = getattr(candidate_profile, 'email', None) if candidate_profile else None

                # Insert candidate record
                candidate_query = text("""
                    INSERT INTO public.candidates 
                    (full_name, email, target_role, experience_level)
                    VALUES 
                    (:full_name, :email, :target_role, :experience_level)
                    RETURNING id;
                """)

                result = await session.execute(
                    candidate_query,
                    {
                        "full_name": parsed_name,
                        "email": candidate_email,
                        "target_role": target_role,
                        "experience_level": experience_level,
                    }
                )
                new_candidate_id = result.scalar_one()

                # Link candidate_id back to public.documents
                update_doc_query = text("""
                    UPDATE public.documents 
                    SET candidate_id = :candidate_id 
                    WHERE id = CAST(:doc_id AS integer);
                """)
                await session.execute(
                    update_doc_query, 
                    {"candidate_id": new_candidate_id, "doc_id": doc_id}
                )

                await session.commit()
                logger.info(f"Successfully inserted candidate '{parsed_name}' and linked to document ID {doc_id}")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in background pipeline for Document ID {doc_id}: {str(e)}")


@router.post("/check-hash", response_model=HashCheckResponse)
async def check_file_hashes(payload: HashCheckRequest, db: AsyncSession = Depends(get_db)):
    if not payload.file_hashes:
        return {"existing_hashes": []}

    query = text("SELECT file_hash FROM public.documents WHERE file_hash = ANY(:hashes)")
    result = await db.execute(query, {"hashes": payload.file_hashes})
    existing_hashes = [row[0] for row in result.fetchall()]
    return {"existing_hashes": existing_hashes}


@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks, 
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None), 
    db: AsyncSession = Depends(get_db)
):
    upload_list = []
    if file:
        upload_list.append(file)
    if files:
        upload_list.extend(files)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No file or files provided in request.")

    processed_records = []

    for f_obj in upload_list:
        content = await f_obj.read()
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        check_query = text("SELECT id, original_name FROM public.documents WHERE file_hash = :hash")
        result = await db.execute(check_query, {"hash": file_hash})
        existing = result.fetchone()

        if existing:
            if len(upload_list) == 1:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Duplicate file hash detected ({existing[1]}). Skipping ingestion."
                )
            continue

        file_ext = os.path.splitext(f_obj.filename)[1]
        storage_name = f"doc_{uuid.uuid4().hex[:12]}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, storage_name)

        with open(file_path, "wb") as f:
            f.write(content)

        insert_query = text("""
            INSERT INTO public.documents (original_name, storage_name, file_path, file_hash, file_size_bytes)
            VALUES (:original_name, :storage_name, :file_path, :file_hash, :file_size_bytes)
            RETURNING id
        """)
        
        insert_result = await db.execute(
            insert_query,
            {
                "original_name": f_obj.filename,
                "storage_name": storage_name,
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size_bytes": file_size,
            }
        )
        doc_id = insert_result.scalar_one()
        await db.commit()

        background_tasks.add_task(
            process_document_vectorization,
            doc_id=doc_id,
            original_name=f_obj.filename,
            file_path=file_path
        )

        processed_records.append({
            "id": str(doc_id),
            "original_name": f_obj.filename,
            "storage_name": storage_name,
            "file_hash": file_hash,
            "status": "ingested"
        })

    return {"status": "success", "files": processed_records}


@router.get("/{document_id}/download")
@router.get("/{document_id}")
async def get_or_download_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches the recorded disk file_path and streams the original file.
    Prioritizes candidate_id lookup first to prevent PK mismatches.
    """
    row = None
    doc_id_str = document_id.strip()

    try:
        if doc_id_str.isdigit():
            target_id = int(doc_id_str)

            # 1. QUERY BY candidate_id FIRST
            query_cand = text("""
                SELECT file_path, original_name 
                FROM public.documents 
                WHERE candidate_id = :target_id
            """)
            res = await db.execute(query_cand, {"target_id": target_id})
            row = res.fetchone()

            # 2. FALLBACK TO document.id ONLY IF NOT FOUND BY candidate_id
            if not row:
                query_doc = text("""
                    SELECT file_path, original_name 
                    FROM public.documents 
                    WHERE id = :target_id
                """)
                res = await db.execute(query_doc, {"target_id": target_id})
                row = res.fetchone()

        else:
            query = text("""
                SELECT file_path, original_name 
                FROM public.documents 
                WHERE id = CAST(:id AS uuid)
            """)
            res = await db.execute(query, {"id": doc_id_str})
            row = res.fetchone()

    except Exception as db_err:
        logger.warning(f"Error querying document by ID ({document_id}): {db_err}")

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Resume file not found for this candidate.")

    file_path, original_name = row[0], row[1]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found on local disk path: {file_path}")

    media_type, _ = mimetypes.guess_type(file_path)
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=original_name,
        media_type=media_type
    )