from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.document import DocumentChunk
from src.schemas.document import DocumentChunkCreate

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chunk(self, chunk_in: DocumentChunkCreate, embedding: list[float]) -> DocumentChunk:
        """
        Saves a single document chunk along with its vector embedding.
        """
        db_chunk = DocumentChunk(
            document_name=chunk_in.document_name,
            language=chunk_in.language,
            content=chunk_in.content,
            embedding=embedding,
            extra_metadata=chunk_in.extra_metadata or {}
        )
        self.db.add(db_chunk)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(db_chunk)
        return db_chunk

    async def create_chunks_batch(self, chunks_in: list[DocumentChunkCreate], embeddings: list[list[float]]) -> list[DocumentChunk]:
        """
        Saves a batch of document chunks efficiently in a single database transaction.
        """
        db_chunks = []
        for chunk_in, embedding in zip(chunks_in, embeddings):
            db_chunk = DocumentChunk(
                document_name=chunk_in.document_name,
                language=chunk_in.language,
                content=chunk_in.content,
                embedding=embedding,
                extra_metadata=chunk_in.extra_metadata or {}
            )
            db_chunks.append(db_chunk)
        
        self.db.add_all(db_chunks)
        await self.db.commit()
        
        for chunk in db_chunks:
            await self.db.refresh(chunk)
            
        return db_chunks

    async def search_similar_chunks(
        self, 
        query_embedding: list[float], 
        language: str | None = None, 
        top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Performs a vector similarity search using Cosine Distance.
        """
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
        
        stmt = select(DocumentChunk, distance_expr.label("distance"))
        
        if language:
            stmt = stmt.where(DocumentChunk.language == language)
            
        stmt = stmt.order_by("distance").limit(top_k)
        
        result = await self.db.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]