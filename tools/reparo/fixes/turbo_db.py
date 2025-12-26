import os
import subprocess
import shutil

def get_pg_config_path():
    try:
        # Tenta pegar o caminho do arquivo de configuracao via psql
        # Assume que psql esta no PATH (o setup.ps1 garante isso)
        cmd = 'psql -U postgres -d isp_monitor -t -c "SHOW config_file;"'
        path = subprocess.check_output(cmd, shell=True).decode().strip()
        if os.path.exists(path):
            return path
    except Exception as e:
        print(f"Erro ao localizar config: {e}")
    return None

def optimize_postgres():
    print("🚀 [TURBO] Iniciando otimizacao do PostgreSQL...")
    
    conf_path = get_pg_config_path()
    if not conf_path:
        print("❌ Erro: Nao foi possivel localizar postgresql.conf. O banco esta rodando?")
        return

    print(f"   Arquivo de configuracao: {conf_path}")
    
    # Backup
    backup_path = conf_path + ".backup_turbo"
    if not os.path.exists(backup_path):
        shutil.copy(conf_path, backup_path)
        print("   ✅ Backup criado.")

    # Configuracoes TURBO (Focadas em performance para Desktop/Dev)
    turbo_settings = {
        "shared_buffers": "512MB",       # Mais memoria para cache
        "work_mem": "16MB",              # Mais memoria para sorts
        "maintenance_work_mem": "256MB", # Manutencao mais rapida
        "effective_cache_size": "2GB",   # Estimativa de cache do OS
        "synchronous_commit": "off",     # MUITO mais rapido (risco minúsculo de perder ultimos msgs se faltar luz)
        "checkpoint_completion_target": "0.9",
        "wal_buffers": "16MB",
        "default_statistics_target": "100",
        "random_page_cost": "1.1",       # Otimizado para SSD
        "effective_io_concurrency": "200" # Otimizado para SSD
    }

    try:
        with open(conf_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        keys_handled = []

        for line in lines:
            line_strip = line.strip()
            if not line_strip or line_strip.startswith('#'):
                new_lines.append(line)
                continue

            # Check if this line is a setting we want to change
            key = line.split('=')[0].strip()
            if key in turbo_settings:
                # Comment out old setting
                new_lines.append(f"# {line.strip()} # Old setting disabled by TURBO\n")
                # Add new setting
                new_lines.append(f"{key} = {turbo_settings[key]}\n")
                keys_handled.append(key)
                print(f"   ⚡ Ajustado: {key} -> {turbo_settings[key]}")
            else:
                new_lines.append(line)

        # Add missing settings
        for key, val in turbo_settings.items():
            if key not in keys_handled:
                new_lines.append(f"\n{key} = {val} # Turbo setting\n")
                print(f"   ⚡ Adicionado: {key} -> {val}")

        with open(conf_path, 'w') as f:
            f.writelines(new_lines)
            
        print("   ✅ Configuracoes aplicadas com sucesso.")
        print("   🔄 Reiniciando servico PostgreSQL...")
        
        subprocess.run("net stop postgresql-x64-15", shell=True) # Tenta versao 15
        subprocess.run("net stop postgresql-x64-16", shell=True) # Tenta versao 16
        subprocess.run("net stop postgresql-x64-17", shell=True) # Tenta versao 17
        subprocess.run("net stop postgresql-x64-18", shell=True) # Tenta versao 18
        
        subprocess.run("net start postgresql-x64-15", shell=True)
        subprocess.run("net start postgresql-x64-16", shell=True)
        subprocess.run("net start postgresql-x64-17", shell=True)
        subprocess.run("net start postgresql-x64-18", shell=True)
        
        print("🚀 [TURBO] Otimizacao concluida! O banco esta voando agora.")

    except Exception as e:
        print(f"❌ Erro ao aplicar configs: {e}")

if __name__ == "__main__":
    optimize_postgres()
    input("\nPressione ENTER para sair...")
