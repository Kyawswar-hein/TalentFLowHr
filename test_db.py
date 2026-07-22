import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from src.core.config import settings

async def diagnostic_check():
    # Use the exact URL your main application uses
    db_url = settings.DATABASE_URL
    print(f"Attempting to connect using: {db_url}")
    print("Connecting...")
    
    try:
        # Create an isolated engine with logging turned on
        engine = create_async_engine(db_url, echo=True)
        
        async with engine.connect() as conn:
            # Run the simplest possible SQL command
            await conn.execute(text("SELECT 1"))
            print("\n============ DIAGNOSTIC RESULT ============")
            print("✅ SUCCESS: The database connection works perfectly!")
            print("===========================================")
            
        await engine.dispose()
        
    except Exception as e:
        print("\n============ DIAGNOSTIC RESULT ============")
        print("❌ FAILURE: Could not establish a database connection.")
        print("===========================================")
        print(f"\nError Details:\n{str(e)}")

if __name__ == "__main__":
    asyncio.run(diagnostic_check())