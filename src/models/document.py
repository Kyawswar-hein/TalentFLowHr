from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from src.core.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    # Primary key using standard autoincrement integer
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Structural metadata
    document_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Bilingual metadata ("en" or "ja") to optimize search routing
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # The actual readable text content snippet
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Vector column. 
    # For standard OpenAI text-embedding-3-small, use 1532 dims (or 3072 for -large)
    # Change vector dimension limit from 1536 to 768
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    
    # Catch-all JSON field for flexible metadata (page numbers, creation dates, tags)
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)