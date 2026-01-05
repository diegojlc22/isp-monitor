"""
Teste Simples - Verificar Insights Gerados
"""
import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Insight, Equipment

async def check_insights():
    print("🤖 ========================================")
    print("🤖 VERIFICAÇÃO DE INSIGHTS DE IA")
    print("🤖 ========================================\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Verificar equipamentos prioritários
        result = await session.execute(
            select(Equipment).where(Equipment.is_priority == True)
        )
        priority_equips = result.scalars().all()
        
        print(f"📊 Equipamentos Prioritários: {len(priority_equips)}")
        for eq in priority_equips:
            print(f"   - {eq.name} ({eq.ip})")
        print()
        
        # 2. Verificar insights gerados
        result = await session.execute(
            select(Insight).where(Insight.is_dismissed == False).order_by(Insight.timestamp.desc())
        )
        insights = result.scalars().all()
        
        print(f"💡 Insights Ativos: {len(insights)}")
        print()
        
        if insights:
            for i, insight in enumerate(insights, 1):
                print(f"[{i}] {insight.insight_type.upper()} - {insight.severity}")
                print(f"    Título: {insight.title}")
                print(f"    Equipamento ID: {insight.equipment_id}")
                print(f"    Data: {insight.timestamp}")
                print()
        else:
            print("ℹ️  Nenhum insight ativo encontrado.")
            print()
            print("💡 Dicas:")
            print("   1. Marque equipamentos como prioritários na aba 'Prioritários'")
            print("   2. Configure limites de tráfego (botão ⚙️)")
            print("   3. Aguarde a próxima análise automática (6h)")
            print("   4. Ou force via API: POST /api/insights/analyze")
    
    print("\n🎉 Verificação completa!")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    asyncio.run(check_insights())
