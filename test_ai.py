"""
Script de Teste - Inteligência de Rede (AI)
Executa análises de segurança e capacidade manualmente
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.database import AsyncSessionLocal
from backend.app.services.security_audit import analyze_security_vulnerabilities
from backend.app.services.capacity_planning import analyze_capacity_trends

async def test_ai():
    print("🤖 ========================================")
    print("🤖 TESTE DE INTELIGÊNCIA DE REDE (AI)")
    print("🤖 ========================================\n")
    
    async with AsyncSessionLocal() as session:
        print("🔒 [1/2] Executando Auditoria de Segurança...")
        try:
            await analyze_security_vulnerabilities()
            print("✅ Auditoria de Segurança concluída!\n")
        except Exception as e:
            print(f"❌ Erro na auditoria: {e}\n")
        
        print("📊 [2/2] Executando Planejamento de Capacidade...")
        try:
            await analyze_capacity_trends()
            print("✅ Planejamento de Capacidade concluído!\n")
        except Exception as e:
            print(f"❌ Erro no planejamento: {e}\n")
    
    print("🎉 ========================================")
    print("🎉 ANÁLISE COMPLETA!")
    print("🎉 ========================================")
    print("\n📋 Acesse a página 'Inteligência' no painel para ver os resultados.")

if __name__ == "__main__":
    asyncio.run(test_ai())
