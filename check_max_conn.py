import asyncio
import asyncpg

async def check():
    try:
        conn = await asyncpg.connect('postgresql://postgres:110812@127.0.0.1:5432/postgres')
        val = await conn.fetchval('show max_connections')
        print(f"Max Connections: {val}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
