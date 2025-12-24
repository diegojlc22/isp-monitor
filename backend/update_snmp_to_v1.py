"""
Migration: Update existing equipments to use SNMP v1 (Ubiquiti compatibility)
"""
import sqlite3
import os

DB_PATH = "monitor.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Count equipments with v2c
        cursor.execute("SELECT COUNT(*) FROM equipments WHERE snmp_version = 2 OR snmp_version IS NULL")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("[INFO] ℹ️  Nenhum equipamento com SNMP v2c encontrado")
            return
        
        print(f"[INFO] 📊 Encontrados {count} equipamento(s) com SNMP v2c")
        print("[INFO] 🔄 Atualizando para SNMP v1...")
        
        # Update to v1
        cursor.execute("UPDATE equipments SET snmp_version = 1 WHERE snmp_version = 2 OR snmp_version IS NULL")
        conn.commit()
        
        print(f"[SUCCESS] ✅ {count} equipamento(s) atualizado(s) para SNMP v1")
        print("[INFO] 💡 Motivo: Compatibilidade com Ubiquiti (v1 funciona, v2c não)")
        
    except Exception as e:
        print(f"[ERROR] ❌ {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*70)
    print("🔄 MIGRATION: Update SNMP version to v1")
    print("="*70)
    migrate()
    print("="*70)
