import os
import shutil
import subprocess
import sys

def install_optimization():
    print("=== INSTALADOR DE PERFORMANCE V2 (TURBO) ===")
    
    # 1. Localizar Pasta de Dados
    pg_versions = ["17", "16", "15"]
    pg_data = None
    service_name = None
    
    for v in pg_versions:
        path = fr"C:\Program Files\PostgreSQL\{v}\data"
        if os.path.exists(path):
            pg_data = path
            service_name = f"postgresql-x64-{v}"
            print(f"[INFO] Banco detectado: PostgreSQL {v}")
            break
            
    if not pg_data:
        print("[ERRO] Instalação padrão do PostgreSQL não encontrada.")
        return

    # 2. Arquivos
    source_conf = "postgresql.conf.optimized"
    target_conf = os.path.join(pg_data, "postgresql.conf")
    backup_conf = os.path.join(pg_data, "postgresql.conf.backup_turbo")
    
    if not os.path.exists(source_conf):
        print("[ERRO] Arquivo de otimização não encontrado na pasta atual.")
        return

    # 3. Backup e Copia
    try:
        shutil.copy2(target_conf, backup_conf)
        print(f"[BACKUP] Configuração original salva em: {os.path.basename(backup_conf)}")
        
        shutil.copy2(source_conf, target_conf)
        print("[COPIA] Configuração OTIMIZADA aplicada.")
        
    except PermissionError:
        print("\n[ERRO CRITICO] ACESSO NEGADO!")
        print("Você precisa executar este script como ADMINISTRADOR.")
        return
    except Exception as e:
        print(f"[ERRO] Falha na cópia: {e}")
        return

    # 4. CORREÇÃO DE PERMISSÕES (Crucial!!!)
    print("[SEGURANCA] Ajustando permissões para o Serviço Windows...")
    try:
        # Resetar ACLs para garantir estado limpo
        subprocess.run(f'icacls "{target_conf}" /reset', shell=True, stdout=subprocess.DEVNULL)
        
        # Dar permissão de leitura para o usuário do serviço
        # O nome do usuário de serviço padrão geralmente é "NT SERVICE\postgresql-x64-17"
        subprocess.run(f'icacls "{target_conf}" /grant "NT SERVICE\\{service_name}":(R)', shell=True, stdout=subprocess.DEVNULL)
        
        print("[SEGURANCA] Permissões aplicadas.")
    except Exception as e:
        print(f"[AVISO] Erro ao ajustar permissões: {e}")

    # 5. Reiniciar
    print("[SERVICO] Reiniciando PostgreSQL...")
    ret_stop = os.system(f"net stop {service_name}")
    ret_start = os.system(f"net start {service_name}")
    
    if ret_start == 0:
        print("\n[SUCESSO] BANCO OTIMIZADO E RODANDO! 🚀")
        print("Agora seu sistema está preparado para alta carga.")
    else:
        print("\n[ERRO] O serviço falhou ao reiniciar.")
        print("Restaurando backup...")
        shutil.copy2(backup_conf, target_conf)
        os.system(f"net start {service_name}")
        print("Backup restaurado. Verifique os logs.")

if __name__ == "__main__":
    install_optimization()
