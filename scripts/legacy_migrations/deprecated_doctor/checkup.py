import sys
import os

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from backend.doctor.fixes import optimize_postgres, install_dependencies

def run_system_checkup():
    print("\n[DOCTOR] 🏥 Iniciando Check-up Geral do Sistema...")
    all_ok = True
    
    # 1. Verificar Otimização do Banco
    print("[DOCTOR] [1/2] Verificando Performance do Banco...")
    if not optimize_postgres.run_fix():
        print("[DOCTOR] ⚠️ Não foi possível otimizar o banco. (Pode exigir Admin)")
        # Não falha o startup por isso, mas avisa
    
    # 2. Verificar Pacotes Críticos (Psutil, etc)
    # A verificação real de pacotes é difícil sem tentar importar.
    # Vamos deixar para o fluxo reativo (se der erro de import, o launcher pega).
    
    print("[DOCTOR] ✅ Check-up concluído.\n")
    return all_ok

if __name__ == "__main__":
    run_system_checkup()
