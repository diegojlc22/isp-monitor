import os
import sys
import subprocess
import glob

# Mapeamento de Erros -> Soluções
ERROR_PATTERNS = {
    "No LID for user": "correcao_whatsapp.bat",
    "Authentication failure": "correcao_whatsapp.bat",
    "Evaluation failed": "correcao_whatsapp.bat",
    "Protocol error": "correcao_whatsapp.bat",
    "ModuleNotFoundError": "instalar_dependencias.bat",
    "ImportError": "instalar_dependencias.bat",
    "EADDRINUSE": "destravar_processos.bat",
    "winerror 10061": "destravar_processos.bat",
    "address already in use": "destravar_processos.bat",
    "TemplateNotFound": "rebuild_frontend.bat",
    "index.html not found": "rebuild_frontend.bat",
    "no such column: equipments.whatsapp_groups": "corrigir_banco.bat",
    "Internal Server Error": "corrigir_banco.bat"
}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIXES_DIR = os.path.join(os.path.dirname(__file__), "fixes")

def scan_logs():
    print("🔍 [DOCTOR] Iniciando diagnostico do sistema...")
    
    logs_to_check = [
        os.path.join(BASE_DIR, "startup.log"),
        os.path.join(BASE_DIR, "api.log"),
        os.path.join(BASE_DIR, "collector.log")
    ]
    
    found_issues = []

    for log_file in logs_to_check:
        if os.path.exists(log_file):
            print(f"   Lendo {os.path.basename(log_file)}...")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Ler apenas os ultimos 5000 chars para pegar erros recentes
                    recent_content = content[-5000:]
                    
                    for error_msg, fix_script in ERROR_PATTERNS.items():
                        if error_msg.lower() in recent_content.lower():
                            if fix_script not in found_issues:
                                print(f"   ⚠️  Encontrado erro critico: '{error_msg}'")
                                found_issues.append(fix_script)
            except Exception as e:
                print(f"   Erro ao ler log: {e}")
    
    return found_issues

def show_menu():
    print("\n[DOCTOR] 🏥 Clinica Geral - Menu de Manutencao")
    print("1. ⚡ Otimizar Banco de Dados (Modo Turbo)")
    print("2. 🏗️  Reconstruir Frontend (Auto-Rebuild)")
    print("3. 🔄 Resetar WhatsApp (Limpeza Profunda)")
    print("4. 💀 Destravar Processos (Force Kill)")
    print("5. 🗄️  Corrigir Estrutura do Banco (Migrations)")
    print("0. Sair")
    
    choice = input("\nEscolha uma opcao: ")
    
    if choice == "1":
        path = os.path.join(FIXES_DIR, "otimizar_banco.bat")
        subprocess.call([path], shell=True)
    elif choice == "2":
        path = os.path.join(FIXES_DIR, "rebuild_frontend.bat")
        subprocess.call([path], shell=True)
    elif choice == "3":
        path = os.path.join(FIXES_DIR, "correcao_whatsapp.bat")
        subprocess.call([path], shell=True)
    elif choice == "4":
        path = os.path.join(FIXES_DIR, "destravar_processos.bat")
        subprocess.call([path], shell=True)
    elif choice == "5":
        path = os.path.join(FIXES_DIR, "corrigir_banco.bat")
        subprocess.call([path], shell=True)

def apply_fixes(fixes):
    if not fixes:
        print("\n✅ [DOCTOR] Nenhum erro critico conhecido encontrado nos logs recentes.")
        print("   O sistema parece saudável.")
        show_menu()
        return

    print(f"\n🚑 [DOCTOR] Encontradas {len(fixes)} solucoes necessarias.")
    
    for fix in fixes:
        script_path = os.path.join(FIXES_DIR, fix)
        if os.path.exists(script_path):
            print(f"\n💉 Executando reparo: {fix}...")
            try:
                subprocess.call([script_path], shell=True)
                print("   ✅ Reparo aplicado.")
            except Exception as e:
                print(f"   ❌ Falha ao aplicar reparo: {e}")
        else:
            print(f"   ❌ Script de reparo nao encontrado: {script_path}")
            
    print("\n✅ [DOCTOR] Ciclo de reparo concluido. Por favor, reinicie o servico.")

if __name__ == "__main__":
    issues = scan_logs()
    apply_fixes(issues)
    input("\nPressione ENTER para sair...")
