import os
import shutil
import subprocess

def is_optimized(conf_path):
    """Verifica se o arquivo já é a versão Turbo"""
    try:
        with open(conf_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(500)
            return "TURBO EDITION" in head
    except:
        return False

def run_fix(arg=None):
    print("[DOCTOR] 🩺 Verificando performance do Banco de Dados...")
    
    # 1. Localizar Pasta de Dados
    pg_versions = ["17", "16", "15"]
    pg_data = None
    service_name = None
    
    for v in pg_versions:
        path = fr"C:\Program Files\PostgreSQL\{v}\data"
        if os.path.exists(path):
            pg_data = path
            service_name = f"postgresql-x64-{v}"
            break
            
    if not pg_data:
        print("[DOCTOR] ⏭️ PostgreSQL padrão não encontrado. Pulando otimização.")
        return True # Não é um erro crítico

    target_conf = os.path.join(pg_data, "postgresql.conf")
    
    # Verifica se já está otimizado
    if is_optimized(target_conf):
        print("[DOCTOR] ✅ Banco de dados já está OTIMIZADO.")
        return True

    print("[DOCTOR] ⚠️ Configuração padrão detectada. Aplicando TURBO MODE...")
    
    # Localizar arquivo fonte
    # Assume que o script roda da raiz do projeto (cwd)
    source_conf = "postgresql.conf.optimized"
    if not os.path.exists(source_conf):
        print("[DOCTOR] ❌ Arquivo fonte de otimização não encontrado.")
        return False

    # Backup e Aplicação
    try:
        shutil.copy2(target_conf, os.path.join(pg_data, "postgresql.conf.backup_auto"))
        shutil.copy2(source_conf, target_conf)
        
        # Permissões (Crucial)
        subprocess.run(f'icacls "{target_conf}" /reset', shell=True, stdout=subprocess.DEVNULL)
        subprocess.run(f'icacls "{target_conf}" /grant "NT SERVICE\\{service_name}":(R)', shell=True, stdout=subprocess.DEVNULL)
        
        print("[DOCTOR] 🔧 Configuração aplicada. Reiniciando serviço...")
        
        subprocess.run(f"net stop {service_name}", shell=True, stdout=subprocess.DEVNULL)
        ret = subprocess.run(f"net start {service_name}", shell=True, capture_output=True)
        
        if ret.returncode == 0:
            print("[DOCTOR] ✅ Otimização aplicada com sucesso!")
            return True
        else:
            print("[DOCTOR] ❌ Falha ao reiniciar serviço pós-otimização. Revertendo...")
            shutil.copy2(os.path.join(pg_data, "postgresql.conf.backup_auto"), target_conf)
            subprocess.run(f"net start {service_name}", shell=True)
            return False
            
    except Exception as e:
        print(f"[DOCTOR] 💥 Falha na otimização: {e}")
        return False

if __name__ == "__main__":
    run_fix()
