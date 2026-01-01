import os
import shutil
import subprocess
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

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
    
    # Check Admin
    if not is_admin():
        print("[DOCTOR] 🛡️ Modo Usuário detectado (Sem Admin).")
        print("[DOCTOR] ⚠️ Para ativar Otimização Turbo do Banco, reinicie como Admin.")
        print("[DOCTOR] ⏭️ Pulando otimização automática para evitar erros...")
        return True # Retorna True para o sistema continuar normalmente
    
    # 1. Localizar Pasta de Dados
    pg_versions = ["20", "19", "18", "17", "16", "15"]
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
    
    # Localizar arquivo fonte (Caminho Absoluto)
    # Sobe 3 níveis a partir de backend/doctor/fixes/ -> Raiz do Projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    source_conf = os.path.join(project_root, "postgresql.conf.optimized")
    
    if not os.path.exists(source_conf):
        print(f"[DOCTOR] ❌ Arquivo fonte não encontrado em: {source_conf}")
        return False

    # Backup e Aplicação
    try:
        shutil.copy2(target_conf, os.path.join(pg_data, "postgresql.conf.backup_auto"))
        shutil.copy2(source_conf, target_conf)
        
        # Permissões (Crucial)
        subprocess.run(f'icacls "{target_conf}" /reset', shell=True, stdout=subprocess.DEVNULL, creationflags=0x08000000)
        subprocess.run(f'icacls "{target_conf}" /grant "NT SERVICE\\{service_name}":(R)', shell=True, stdout=subprocess.DEVNULL, creationflags=0x08000000)
        
        print("[DOCTOR] 🔧 Configuração aplicada. Reiniciando serviço...")
        
        subprocess.run(f"net stop {service_name}", shell=True, stdout=subprocess.DEVNULL, creationflags=0x08000000)
        ret = subprocess.run(f"net start {service_name}", shell=True, capture_output=True, creationflags=0x08000000)
        
        if ret.returncode == 0:
            print("[DOCTOR] ✅ Otimização aplicada com sucesso!")
            return True
        else:
            print("[DOCTOR] ❌ Otimização FALHOU ao reiniciar serviço. O Postgres recusou a config.")
            print("[DOCTOR] ℹ️ Verifique se tem RAM livre suficiente ou reduza 'shared_buffers'.")
            
            shutil.copy2(os.path.join(pg_data, "postgresql.conf.backup_auto"), target_conf)
            subprocess.run(f"net start {service_name}", shell=True, creationflags=0x08000000)
            print("[DOCTOR] ℹ️ Sistema restaurado para padrão.")
            return True
            
    except Exception as e:
        print(f"[DOCTOR] 💥 Falha na otimização: {e}")
        return True # Retorna TRUE para continuar mesmo sem otimização

if __name__ == "__main__":
    run_fix()
