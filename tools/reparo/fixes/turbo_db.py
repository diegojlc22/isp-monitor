import os
import subprocess
import shutil

def find_psql_executable():
    # Locais comuns onde o Postgres instala
    candidates = [
        r"C:\Program Files\PostgreSQL\20\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\19\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return f'"{path}"' # Retorna com aspas
    
    # Se nao achou, tenta o padrao do path
    return "psql"

def get_pg_config_path():
    # Definir senha para evitar prompt interativo
    os.environ["PGPASSWORD"] = "110812"
    
    try:
        psql_cmd = find_psql_executable()
        print(f"   [DEBUG] Usando cliente Postgres: {psql_cmd}")
        
        # Tenta pegar o caminho do arquivo de configuracao
        # Precisamos passar senha PGPASSWORD se nao estiver confiado, mas assumimos 'trust' local
        cmd = f'{psql_cmd} -U postgres -d isp_monitor -t -c "SHOW config_file;"'
        
        path = subprocess.check_output(cmd, shell=True).decode().strip()
        if os.path.exists(path):
            return path
    except Exception as e:
        print(f"Erro ao localizar config: {e}")
        # Fallback: Tentar adivinhar caminho padrao
        fallback_paths = [
            r"C:\Program Files\PostgreSQL\17\data\postgresql.conf",
            r"C:\Program Files\PostgreSQL\16\data\postgresql.conf",
            r"C:\Program Files\PostgreSQL\15\data\postgresql.conf"
        ]
        for p in fallback_paths:
            if os.path.exists(p):
                print(f"   [AVISO] Detectado via Fallback: {p}")
                return p
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
        
        # Detectar versao baseada no caminho (Ex: .../18/data...)
        version = "16" # Default seguro
        if "/18/" in conf_path.replace("\\", "/"): version = "18"
        elif "/17/" in conf_path.replace("\\", "/"): version = "17"
        elif "/16/" in conf_path.replace("\\", "/"): version = "16"
        elif "/15/" in conf_path.replace("\\", "/"): version = "15"
        
        service_name = f"postgresql-x64-{version}"
        print(f"   [INFO] Reiniciando serviço detectado: {service_name}")
        
        # Reiniciar apenas o servico correto
        subprocess.run(f"net stop {service_name}", shell=True)
        subprocess.run(f"net start {service_name}", shell=True)
        
        print("🚀 [TURBO] Otimizacao concluida! O banco esta voando agora.")

    except Exception as e:
        print(f"❌ Erro ao aplicar configs: {e}")

if __name__ == "__main__":
    optimize_postgres()
    input("\nPressione ENTER para sair...")
