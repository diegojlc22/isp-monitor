import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def migration():
    async with engine.begin() as conn:
        print("Verificando colunas de voltagem...")
        # Adiciona colunas se não existirem
        await conn.execute(text("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='voltage_multiplier') THEN
                    ALTER TABLE equipments ADD COLUMN voltage_multiplier FLOAT DEFAULT 1.0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='equipments' AND column_name='voltage_offset') THEN
                    ALTER TABLE equipments ADD COLUMN voltage_offset FLOAT DEFAULT 0.0;
                END IF;
            END $$;
        """))
        print("✅ Banco de dados atualizado para suportar calibração!")

if __name__ == "__main__":
    asyncio.run(migration())
