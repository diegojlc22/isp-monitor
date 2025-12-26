import os
import subprocess
import sys

def run_fix():
    print("[DOCTOR] 🩺 Diagnóstico: Problema no Serviço PostgreSQL detectado.")
    print("[DOCTOR] 🩹 Iniciando protocolo de reparo...")

    # 1. Identificar Versão e Caminho
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
        print("[DOCTOR] ❌ Instalação padrão do PostgreSQL não encontrada.")
        return False
        
    print(f"[DOCTOR] 🎯 Alvo identificado: {service_name}")
    
    # 2. Correção de Permissões (Principal causa de falha "inicia e para")
    print("[DOCTOR] 🔧 Ajustando permissões de arquivo (ICACLS)...")
    conf_file = os.path.join(pg_data, "postgresql.conf")
    try:
        # Resetar e garantir leitura para o serviço
        subprocess.run(f'icacls "{conf_file}" /reset', shell=True, stdout=subprocess.DEVNULL)
        subprocess.run(f'icacls "{conf_file}" /grant "NT SERVICE\\{service_name}":(R)', shell=True, stdout=subprocess.DEVNULL)
        subprocess.run(f'icacls "{pg_data}" /grant "NT SERVICE\\{service_name}":(R)', shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"[DOCTOR] ⚠️ Aviso ao ajustar permissões: {e}")

    # 3. Reiniciar Serviço
    print("[DOCTOR] ⚡ Tentando reiniciar o serviço...")
    # Tenta parar primeiro para garantir
    subprocess.run(f"net stop {service_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    res = subprocess.run(f"net start {service_name}", shell=True, capture_output=True)
    output = res.stdout.decode('cp850', errors='ignore') + res.stderr.decode('cp850', errors='ignore')
    
    if res.returncode == 0:
        print("[DOCTOR] ✅ Serviço PostgreSQL REPARADO e INICIADO com sucesso!")
        return True
    elif "já foi iniciado" in output:
        print("[DOCTOR] ✅ Serviço já estava rodando.")
        return True
    
    print(f"[DOCTOR] ❌ Falha ao iniciar serviço: {output.strip()}")
    print("[DOCTOR] 💡 Dica: O reparo pode exigir privilégios de Administrador.")
    return False

if __name__ == "__main__":
    if run_fix():
        sys.exit(0)
    else:
        sys.exit(1)
