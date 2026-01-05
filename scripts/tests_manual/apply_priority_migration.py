"""
Apply is_priority migration
"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.app.database import AsyncSessionLocal
from sqlalchemy import text

async def apply_migration():
    async with AsyncSessionLocal() as session:
        # Add column
        await session.execute(text("""
            ALTER TABLE equipments 
            ADD COLUMN IF NOT EXISTS is_priority BOOLEAN DEFAULT FALSE
        """))
        
        # Create index
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_equipments_is_priority 
            ON equipments(is_priority) WHERE is_priority = TRUE
        """))
        
        await session.commit()
        print("✅ Migration applied successfully!")
        print("   - Added is_priority column")
        print("   - Created index for performance")

if __name__ == "__main__":
    asyncio.run(apply_migration())
