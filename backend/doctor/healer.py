import os
import sys
import importlib.util

# --- REGISTRO DE DOENÇAS E CURAS ---
# Mapeia strings encontradas no LOG -> Nome do Arquivo de Correção (na pasta fixes/)
SYMPTOM_REGISTRY = [
    {
        "triggers": [
            "ConnectionRefusedError", 
            "create_connection", 
            "asyncpg.exceptions.CannotConnectNowError",
            "remote computer refused the network connection",
            "computador remoto recusou a conexão",
            "Connect call failed"
        ],
        "fix_script": "fix_postgres_service.py",
        "description": "Reparar Serviço PostgreSQL"
    },
    {
        "triggers": ["ModuleNotFoundError", "ImportError"],
        "fix_script": "install_dependencies.py",
        "description": "Instalar Dependências Faltando",
        "pass_log_to_script": True # Esse script precisa ler o log pra saber qual pacote
    },
    {
        "triggers": ["unrecognized winsock error 10054", "server closed the connection unexpectedly"],
        "fix_script": "fix_postgres_service.py", # Geralmente restart resolve
        "description": "Reiniciar PostgreSQL (Erro de Socket)"
    }
]

def load_fix_module(script_name):
    """Carrega dinamicamente um modulo da pasta fixes"""
    try:
        fixes_dir = os.path.join(os.path.dirname(__file__), "fixes")
        script_path = os.path.join(fixes_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"[DOCTOR] Script de cura não encontrado: {script_name}")
            return None
            
        spec = importlib.util.spec_from_file_location("fix_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"[DOCTOR] Erro ao carregar cura: {e}")
        return None

def diagnose_and_heal(log_chunk):
    """
    Analisa um trecho de log e tenta aplicar uma correção.
    Retorna True se uma correção foi aplicada com sucesso.
    """
    print("\n[DOCTOR] 🩺 Analisando sintomas...")
    
    for entry in SYMPTOM_REGISTRY:
        for trigger in entry["triggers"]:
            if trigger.lower() in log_chunk.lower():
                print(f"[DOCTOR] 🔬 Sintoma identificado: '{trigger}'")
                print(f"[DOCTOR] 💊 Tratamento recomendado: {entry['description']}")
                
                module = load_fix_module(entry["fix_script"])
                if not module:
                    return False
                
                try:
                    # Executa a cura
                    if entry.get("pass_log_to_script"):
                        success = module.run_fix(log_chunk)
                    else:
                        success = module.run_fix()
                        
                    if success:
                        print("[DOCTOR] ✨ Tratamento aplicado com SUCESSO! O sistema deve se recuperar.")
                        return True
                    else:
                        print("[DOCTOR] ⚠️ O tratamento falhou. Intervenção humana necessária.")
                        return False
                        
                except Exception as e:
                    print(f"[DOCTOR] 💥 Erro durante o tratamento: {e}")
                    return False
                    
    print("[DOCTOR] 🤷 Nenhum sintoma conhecido identificado nos logs.")
    return False

if __name__ == "__main__":
    # Teste de linha de comando
    if len(sys.argv) > 1:
        log_sample = sys.argv[1]
        diagnose_and_heal(log_sample)
    else:
        print("Uso: python healer.py \"string de erro do log\"")
