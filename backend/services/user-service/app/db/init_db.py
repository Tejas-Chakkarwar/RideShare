import asyncio
from app.db.session import engine
from app.db.base import Base
# Import all models so Base knows about them for table creation
from app.models.user import User

async def init_db():
    async with engine.begin() as conn:
        # Check if we should drop tables (Dangerous!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
