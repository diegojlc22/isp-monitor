
import os
import subprocess
from datetime import datetime

# Configuração
DB_NAME = "isp_monitor"
DB_USER = "postgres"
BACKUP_DIR = "backups"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_FILE = os.path.join(BACKUP_DIR, f"backup_full_{TIMESTAMP}.sql")

def run_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    print(f"[BACKUP] Iniciando backup completo de '{DB_NAME}'...")
    print(f"[BACKUP] Arquivo alvo: {BACKUP_FILE}")
    
    # Comando pg_dump para incluir dados de todas as partições
    # O parametro --format=p (plain) ou -F c (custom) pegam tudo.
    # O importante é garantir que CREATE TABLE das partitions existam.
    # O pg_dump padrão já lida com particionamento nativo.
    cmd = f"pg_dump -U {DB_USER} -h localhost -F c -b -v -f \"{BACKUP_FILE}\" {DB_NAME}"
    
    # Nota: Senha deve estar no .pgpass ou variável de ambiente PGPASSWORD
    # Para teste rápido, vamos assumir que o ambiente tem acesso ou .pgpass
    # Se falhar, avisa.
    
    try:
        # Definindo PGPASSWORD apenas para este subprocesso (Inseguro para prod compartilhado, ok para script local)
        env = os.environ.copy()
        env["PGPASSWORD"] = "110812" # Hardcoded based on project config for simplicity
        
        process = subprocess.run(cmd, shell=True, env=env, check=True)
        print("[BACKUP] ✅ Backup realizado com sucesso!")
        
        # Validar tamanho
        size = os.path.getsize(BACKUP_FILE)
        print(f"[BACKUP] Tamanho do arquivo: {size / 1024 / 1024:.2f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"[BACKUP] ❌ Falha no pg_dump: {e}")
    except Exception as e:
        print(f"[BACKUP] ❌ Erro inesperado: {e}")

if __name__ == "__main__":
    run_backup()
