from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models import Equipment, PingStatsHourly
from backend.app.services.reports import generate_sla_pdf
from backend.app.dependencies import get_current_user
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/sla/pdf")
async def get_sla_report_pdf(days: int = 30, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Gera um PDF com o relatório de SLA dos últimos X dias.
    """
    try:
        # Calcular período
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        # Fix for DBAPIError: can't subtract offset-naive and offset-aware datetimes
        # The DB column is naive (UTC), so we must compare with naive datetime
        start_date = start_date.replace(tzinfo=None)
        
        # Buscar estatísticas agregadas (PingStatsHourly)
        # Queremos a média de disponibilidade POR equipamento no período
        
        stmt = select(
            PingStatsHourly.device_id,
            func.avg(PingStatsHourly.availability_percent).label('avg_uptime'),
            func.avg(PingStatsHourly.avg_latency_ms).label('avg_latency')
        ).where(
            PingStatsHourly.timestamp >= start_date
        ).group_by(PingStatsHourly.device_id)
        
        stats_result = await db.execute(stmt)
        stats_rows = stats_result.all()
        
        # Mapear stats em um dict para acesso rápido
        stats_map = {row.device_id: row for row in stats_rows}
        
        # Buscar equipamentos para ter nomes
        # Apenas monitorados (tem IP)
        equipments_result = await db.execute(select(Equipment).where(Equipment.ip != None))
        equipments = equipments_result.scalars().all()
        
        report_data = []
        for eq in equipments:
            stat = stats_map.get(eq.id)
            
            # Se não tem stats históricos, usar dados atuais ou 0
            # (Para ser justo, se não tem histórico, talvez não deva aparecer ou mostrar N/A)
            uptime = round(stat.avg_uptime, 2) if stat else 0.0
            latency = round(stat.avg_latency, 2) if stat else 0.0
            
            report_data.append({
                "name": eq.name,
                "ip": eq.ip,
                "availability_percent": uptime,
                "avg_latency_ms": latency
            })
            
        # Ordenar por menor disponibilidade (os problemas primeiro)
        report_data.sort(key=lambda x: x['availability_percent'])
        
        # Gerar PDF
        period_str = f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
        pdf_buffer = generate_sla_pdf(report_data, period_str)
        
        headers = {
            'Content-Disposition': f'attachment; filename="Relatorio_SLA_ISP_{datetime.now().strftime("%Y%m%d")}.pdf"'
        }
        
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except Exception as e:
        print(f"Erro gerando relatório: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF")
