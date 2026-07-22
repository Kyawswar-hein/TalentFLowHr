from src.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = settings.DATABASE_URL

# Create the async engine with connection pooling optimized for FastAPI
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True if you want to see raw SQL logs during development
    pool_size=10,
    max_overflow=20,
)

# Session factory for generating isolated database transactions per request
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for your SQLAlchemy models (metadata tracking)
class Base(DeclarativeBase):
    pass

# FastAPI Dependency to yield database sessions safely
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()