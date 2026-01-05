"""
Força Análise de IA Manualmente
"""
import asyncio
from backend.app.services.security_audit import run_security_audit
from backend.app.services.capacity_planning import analyze_capacity_trends

async def force_ai_analysis():
    print("🤖 ========================================")
    print("🤖 FORÇANDO ANÁLISE DE IA")
    print("🤖 ========================================\n")
    
    # 1. Auditoria de Segurança
    print("🔒 [1/2] Executando Auditoria de Segurança...")
    try:
        await run_security_audit()
        print("✅ Auditoria concluída!\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    # 2. Planejamento de Capacidade
    print("📊 [2/2] Executando Planejamento de Capacidade...")
    try:
        await analyze_capacity_trends()
        print("✅ Planejamento concluído!\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    print("🎉 ========================================")
    print("🎉 ANÁLISE COMPLETA!")
    print("🎉 ========================================")
    print("\n💡 Execute 'python check_insights.py' para ver os resultados")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    asyncio.run(force_ai_analysis())
