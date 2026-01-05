import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("🚀 Starting PostgreSQL Migrations...")
        
        # 1. Update 'equipments' table
        print("Checking 'equipments' columns...")
        try:
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN max_traffic_in FLOAT"))
            print("Added max_traffic_in to equipments")
        except Exception as e: print(f"max_traffic_in: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN max_traffic_out FLOAT"))
            print("Added max_traffic_out to equipments")
        except Exception as e: print(f"max_traffic_out: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN last_traffic_alert_sent TIMESTAMP"))
            print("Added last_traffic_alert_sent to equipments")
        except Exception as e: print(f"last_traffic_alert_sent: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN traffic_alert_interval INTEGER DEFAULT 360"))
            print("Added traffic_alert_interval to equipments")
        except Exception as e: print(f"traffic_alert_interval: {e}")

        # 2. Update 'network_links' table
        print("\nChecking 'network_links' columns...")
        try:
            await conn.execute(text("ALTER TABLE network_links ADD COLUMN source_equipment_id INTEGER"))
            print("Added source_equipment_id to network_links")
        except Exception as e: print(f"source_equipment_id: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE network_links ADD COLUMN target_equipment_id INTEGER"))
            print("Added target_equipment_id to network_links")
        except Exception as e: print(f"target_equipment_id: {e}")

        # 3. Create 'insights' table if not exists
        print("\nChecking 'insights' table...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS insights (
                    id SERIAL PRIMARY KEY,
                    insight_type VARCHAR(50),
                    severity VARCHAR(20),
                    equipment_id INTEGER REFERENCES equipments(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    message TEXT,
                    recommendation TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_dismissed BOOLEAN DEFAULT FALSE
                )
            """))
            print("Insights table checked/created")
        except Exception as e: print(f"insights table: {e}")
        
        print("\n✅ Migration Finished")

if __name__ == "__main__":
    asyncio.run(migrate())
