import csv
import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Adicionar pasta raiz ao path para importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.models import Tower
from backend.app.database import DATABASE_URL

# Ajustar URL do banco para driver async se necessário
if "postgresql://" in DATABASE_URL and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Fallback se a URL vier vazia (desenvolvimento local)
if not DATABASE_URL:
    print("[!] DATABASE_URL não encontrada. Tentando padrão local...")
    DATABASE_URL = "postgresql+asyncpg://postgres:110812@localhost/isp_monitor"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def clean_float(value):
    """Converte string com virgula ou ponto para float valido"""
    if not value or not isinstance(value, str): return None
    value = value.strip()
    if not value: return None
    try:
        return float(value.replace(',', '.'))
    except:
        return None

async def import_csv(file_path):
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo não encontrado: {file_path}")
        return

    print(f"[*] Lendo arquivo: {file_path}...")
    
    count_new = 0
    count_skip = 0
    
    async with AsyncSessionLocal() as session:
        try:
            # Tenta detectar dialeto (separador , ; ou \t)
            with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
                # Ler uma amostra para detectar
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                except:
                    # Fallback padrão se falhar
                    class Dialect(csv.Dialect):
                        delimiter = '\t' # Tenta TAB por padrão se der erro, parece ser o caso
                        quotechar = '"'
                        doublequote = True
                        skipinitialspace = True
                        lineterminator = '\n'
                        quoting = csv.QUOTE_MINIMAL
                    dialect = Dialect

                reader = csv.DictReader(csvfile, dialect=dialect)
                
                # Normalizar cabeçalhos (remover espaços e lower case)
                # Mapeamento de sinonimos
                normalized_fieldnames = []
                if reader.fieldnames:
                    for field in reader.fieldnames:
                        f = field.lower().strip()
                        if f in ['descrição', 'descricao', 'obs']: f = 'observacoes'
                        if f in ['lat']: f = 'latitude'
                        if f in ['lon', 'long']: f = 'longitude'
                        normalized_fieldnames.append(f)
                    reader.fieldnames = normalized_fieldnames
                
                print(f"[*] Colunas detectadas: {reader.fieldnames}")

                if 'nome' not in reader.fieldnames:
                    print("[ERRO] O arquivo precisa ter pelo menos a coluna 'Nome'.")
                    print(f"      Encontrado: {reader.fieldnames}")
                    return

                for row in reader:
                    name = row.get('nome', '').strip()
                    if not name: continue
                    
                    # Tenta pegar latitude/longitude
                    lat = clean_float(row.get('latitude'))
                    lon = clean_float(row.get('longitude'))
                    obs = row.get('observacoes') or row.get('descricao')
                    ip = row.get('ip')
                    
                    # Se IP vier vazio
                    ip = ip.strip() if ip and ip.strip() else None

                    # Verificar se já existe
                    stmt = select(Tower).where(Tower.name == name)
                    result = await session.execute(stmt)
                    existing = result.scalars().first()
                    
                    if existing:
                        print(f"[-] Pular: '{name}' já existe.")
                        count_skip += 1
                        # Se quiser ATUALIZAR coordenadas de existentes, descomente abaixo:
                        # if lat and lon:
                        #     existing.latitude = lat
                        #     existing.longitude = lon
                        #     session.add(existing)
                    else:
                        new_tower = Tower(
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            ip=ip, # Se não tiver na planilha, fica null
                            observations=obs,
                            is_online=True
                        )
                        session.add(new_tower)
                        count_new += 1
                        print(f"[+] Cadastrando: '{name}' ({lat}, {lon})")
            
            await session.commit()
            print("\n========================================")
            print(f"IMPORTAÇÃO CONCLUÍDA!")
            print(f"Novas Torres: {count_new}")
            print(f"Já Existiam: {count_skip}")
            print("========================================")
            
        except Exception as e:
            print(f"\n[ERRO CRÍTICO] Falha na importacao: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    target_file = "torres.csv"
    
    # Se rodar de dentro da pasta scripts
    if not os.path.exists(target_file):
        target_file = "../torres.csv"
    
    # Se usuário passou argumento
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        
    if os.path.exists(target_file):
        asyncio.run(import_csv(target_file))
    else:
        print("[!] Arquivo 'torres.csv' não encontrado.")
        print("    Crie um arquivo 'torres.csv' com colunas: Nome, Latitude, Longitude")
