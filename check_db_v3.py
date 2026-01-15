
import psycopg2

def check_db():
    conn_params = {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "isp_monitor",
        "user": "postgres",
        "password": "110812"
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Check equipments columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='equipments'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Columns in 'equipments': {columns}")
        
        if 'ai_overrides' in columns:
            print("✅ A coluna ai_overrides EXISTE!")
        else:
            print("❌ A coluna ai_overrides NÃO EXISTE!")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_db()
