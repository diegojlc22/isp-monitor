"""
Script para aplicar otimizações de performance no banco de dados.
Executa o arquivo SQL com índices e análises.

Uso:
    python apply_performance_indexes.py
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from sqlalchemy import text


async def apply_indexes():
    """Aplica os índices de performance no banco de dados"""
    
    sql_file = backend_dir / "sql" / "performance_indexes.sql"
    
    if not sql_file.exists():
        print(f"❌ Arquivo SQL não encontrado: {sql_file}")
        return False
    
    print("📊 Aplicando otimizações de performance...")
    print(f"📁 Arquivo: {sql_file}")
    print()
    
    # Ler o arquivo SQL
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Dividir em statements individuais (separados por ;)
    raw_statements = sql_content.split(';')
    
    statements = []
    for raw in raw_statements:
        # Remover linhas de comentário e whitespace
        lines = [line for line in raw.split('\n') if line.strip() and not line.strip().startswith('--')]
        clean_statement = ' '.join(lines).strip()
        if clean_statement:
            statements.append(clean_statement)

    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i, statement in enumerate(statements, 1):
             # Logica de execucao ja trata o statement limpo
            
            try:
                # Extrair nome do índice para log
                index_name = "statement"
                if "CREATE INDEX" in statement:
                    parts = statement.split()
                    if "IF NOT EXISTS" in statement:
                        idx = parts.index("EXISTS") + 1
                        index_name = parts[idx] if idx < len(parts) else "unknown"
                    else:
                        idx = parts.index("INDEX") + 1
                        index_name = parts[idx] if idx < len(parts) else "unknown"
                elif "ANALYZE" in statement:
                    index_name = f"ANALYZE {statement.split()[1]}"
                
                print(f"⏳ [{i}/{len(statements)}] Executando: {index_name}...", end=' ')
                
                await conn.execute(text(statement))
                
                print("✅")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                # Ignorar erro de índice já existente
                if "already exists" in error_msg.lower():
                    print("⚠️  (já existe)")
                    success_count += 1
                else:
                    print(f"❌ Erro: {error_msg}")
                    error_count += 1
    
    print()
    print("=" * 60)
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print("=" * 60)
    
    if error_count == 0:
        print()
        print("🎉 Todas as otimizações foram aplicadas com sucesso!")
        print()
        print("📈 Impacto esperado:")
        print("   • Queries 50-80% mais rápidas")
        print("   • Filtros por status/torre/tipo otimizados")
        print("   • Histórico de latência mais rápido")
        print("   • Validação de IP duplicado instantânea")
        print()
        print("💡 Próximos passos:")
        print("   1. Reiniciar o backend para garantir uso dos índices")
        print("   2. Monitorar performance com EXPLAIN ANALYZE")
        print("   3. Verificar tamanho dos índices (não deve exceder 10% da tabela)")
        return True
    else:
        print()
        print("⚠️  Algumas otimizações falharam. Verifique os erros acima.")
        return False


async def verify_indexes():
    """Verifica quais índices foram criados"""
    
    print()
    print("🔍 Verificando índices criados...")
    print()
    
    query = text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
    """)
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("❌ Nenhum índice encontrado")
            return
        
        current_table = None
        for row in rows:
            table = row[1]
            index = row[2]
            
            if table != current_table:
                print()
                print(f"📋 Tabela: {table}")
                current_table = table
            
            print(f"   ✓ {index}")
        
        print()
        print(f"📊 Total: {len(rows)} índices")


async def main():
    # Aplicar índices
    success = await apply_indexes()
    
    if success:
        # Verificar índices criados
        await verify_indexes()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ISP Monitor - Performance Optimization")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(main())
        
        print()
        print("=" * 60)
        print("✅ Script concluído")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print()
        print("⚠️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
