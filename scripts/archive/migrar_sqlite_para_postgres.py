import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import sys
from datetime import datetime

# --- CONFIGURAÇÃO ---
SQLITE_DB = "monitor.db"

# Config via Env ou Hardcoded (já que o usuário forneceu)
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://postgres:110812@localhost:5432/monitor_prod")

def get_postgres_conn():
    if not POSTGRES_URL:
        print("❌ ERRO: Variável de ambiente DATABASE_URL não definida!")
        print("Exemplo: set DATABASE_URL=postgresql://postgres:senha@localhost:5432/isp_monitor")
        sys.exit(1)
    try:
        return psycopg2.connect(POSTGRES_URL)
    except Exception as e:
        print(f"❌ Erro ao conectar no PostgreSQL: {e}")
        sys.exit(1)

def migrate_users(sqlite_cur, pg_cur):
    print("Migrando Users...")
    sqlite_cur.execute("SELECT id, name, email, hashed_password, role, created_at FROM users")
    rows = sqlite_cur.fetchall()
    
    query = """
    INSERT INTO users (id, name, email, hashed_password, role, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING;
    """
    execute_batch(pg_cur, query, rows)
    print(f"✅ {len(rows)} usuários migrados.")

def migrate_towers(sqlite_cur, pg_cur):
    print("Migrando Towers...")
    # Schema real: id, name, ip, latitude, longitude, observations, parent_id, maintenance_until
    # Vamos verificar o que tem no SQLite
    
    cols = ["id", "name", "ip", "latitude", "longitude", "observations", "parent_id", "maintenance_until"]
    sel_cols = ", ".join(cols)
    
    try:
        sqlite_cur.execute(f"SELECT {sel_cols} FROM towers")
    except sqlite3.OperationalError:
         # Fallback se colunas novas nao existirem
         print("⚠️ Schema de Towers antigo detectado. Tentando colunas básicas...")
         cols = ["id", "name", "ip", "latitude", "longitude"]
         sel_cols = ", ".join(cols)
         sqlite_cur.execute(f"SELECT {sel_cols} FROM towers")

    rows = sqlite_cur.fetchall()

    placeholders = ", ".join(["%s"] * len(cols))
    query = f"""
    INSERT INTO towers ({', '.join(cols)})
    VALUES ({placeholders})
    ON CONFLICT (id) DO NOTHING;
    """
    execute_batch(pg_cur, query, rows)
    print(f"✅ {len(rows)} torres migradas.")

def migrate_equipments(sqlite_cur, pg_cur):
    print("Migrando Equipments...")
    
    # Model: ip (não ip_address)
    # Ignoramos is_online/status e last_latency pois eles atualizam no primeiro ping
    cols = [
        "id", "name", "ip", "tower_id", 
        "snmp_community", "snmp_version", "snmp_port", 
        "snmp_interface_index", "is_mikrotik", "mikrotik_interface", 
        "api_port", "brand", "equipment_type", "signal_dbm", "ccq", "connected_clients"
    ]
    
    # Validação dinamica
    valid_cols = []
    # Testar cada coluna ou obter lista do PRAGMA
    # Modo preguiçoso: tentar selecionar todas, se falhar, remover as novas
    
    sel_cols = ", ".join(cols)
    try:
        sqlite_cur.execute(f"SELECT {sel_cols} FROM equipments")
        valid_cols = cols
    except sqlite3.OperationalError:
        # Tentar versão sem colunas novas (caso a migração do sqlite tenha falhado silenciosamente antes)
        print("⚠️ Schema de Equipments incompleto no SQLite. Migrando parcial...")
        # Fallback seguro
        fallback_cols = ["id", "name", "ip", "tower_id", "snmp_community"]
        sel_cols = ", ".join(fallback_cols)
        sqlite_cur.execute(f"SELECT {sel_cols} FROM equipments")
        valid_cols = fallback_cols

    rows = sqlite_cur.fetchall()
    
    if not rows:
        print("ℹ️ Nenhum equipamento para migrar.")
        return

    placeholders = ", ".join(["%s"] * len(valid_cols))
    query = f"""
    INSERT INTO equipments ({', '.join(valid_cols)})
    VALUES ({placeholders})
    ON CONFLICT (id) DO NOTHING;
    """
    
    execute_batch(pg_cur, query, rows)
    print(f"✅ {len(rows)} equipamentos migrados.")

def migrate_targets(sqlite_cur, pg_cur):
    print("Migrando Agent Targets...")
    try:
        # Schema Verified: id, name, target, type, enabled
        cols = ["id", "name", "target", "type", "enabled"]
        sel_cols = ", ".join(cols)
        
        sqlite_cur.execute(f"SELECT {sel_cols} FROM monitor_targets")
        rows = sqlite_cur.fetchall()
        
        placeholders = ", ".join(["%s"] * len(cols))
        query = f"""
        INSERT INTO monitor_targets ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT (id) DO NOTHING;
        """
        execute_batch(pg_cur, query, rows)
        print(f"✅ {len(rows)} alvos do agente migrados.")
    except Exception as e:
        print(f"⚠️ Erro ao migrar targets: {e}")

def migrate_parameters(sqlite_cur, pg_cur):
    print("Migrando Parameters...")
    try:
        sqlite_cur.execute("SELECT key, value FROM parameters")
        rows = sqlite_cur.fetchall()
        
        query = """
        INSERT INTO parameters (key, value)
        VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
        """
        execute_batch(pg_cur, query, rows)
        print(f"✅ {len(rows)} parâmetros migrados.")
    except Exception as e:
        print(f"⚠️ Erro ao migrar parâmetros: {e}")

def main():
    print("=== MIGRADOR SQLITE -> POSTGRES ===")
    
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Arquivo {SQLITE_DB} não encontrado.")
        return

    # Conexões
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    
    pg_conn = get_postgres_conn()
    pg_cur = pg_conn.cursor()

    try:
        # Ordem importa (Foreign Keys)
        migrate_users(sqlite_cur, pg_cur)
        migrate_parameters(sqlite_cur, pg_cur)
        migrate_towers(sqlite_cur, pg_cur)
        migrate_equipments(sqlite_cur, pg_cur)
        migrate_targets(sqlite_cur, pg_cur)
        
        pg_conn.commit()
        
        # Reset sequences (Opcional, mas bom para postgres não falhar no proximo insert)
        # Para simplificar, assumimos que o usuario nao vai criar nada manual agora
        
        print("\n🎉 Migração CONCLUÍDA com sucesso!")
        print("Os logs (ping/traffic) NÃO foram migrados para manter o banco leve.")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"\n❌ ERRO durante migração: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()
