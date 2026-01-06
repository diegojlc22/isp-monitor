from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models import Equipment, PingStatsHourly, Alert
from backend.app.services.reports import generate_sla_pdf, generate_incidents_pdf
from backend.app.dependencies import get_current_user
from datetime import datetime, timedelta, timezone
from backend.app.config import logger

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
            
        # Calcular estatísticas globais
        total_uptime = 0
        total_latency = 0
        critical_devices_count = 0
        count = 0
        
        for item in report_data:
            up = item['availability_percent']
            lat = item['avg_latency_ms']
            
            total_uptime += up
            total_latency += lat
            count += 1
            
            if up < 99.0:
                critical_devices_count += 1
                
        global_uptime = round(total_uptime / count, 2) if count > 0 else 0
        global_latency = round(total_latency / count, 2) if count > 0 else 0
        
        # Gerar Conclusão
        conclusion = ""
        if global_uptime >= 99.9:
            conclusion = "✅ <b>Excelência Operacional!</b> A rede atingiu níveis de estabilidade de classe mundial, superando as metas de SLA (99.9%)."
        elif global_uptime >= 99.0:
            conclusion = "✅ <b>Meta Atingida.</b> A rede operou dentro dos parâmetros esperados de qualidade (SLA > 99%)."
        elif global_uptime >= 95.0:
            conclusion = f"⚠️ <b>Atenção Necessária.</b> A disponibilidade média ({global_uptime}%) está abaixo da meta ideal (99%). {critical_devices_count} dispositivos apresentaram instabilidade significativa."
        else:
            conclusion = f"🚨 <b>Crítico.</b> A rede enfrentou severos problemas de disponibilidade ({global_uptime}%), impactando fortemente a operação. Ação imediata é recomendada nos {critical_devices_count} dispositivos críticos."

        stats = {
            "global_uptime": global_uptime,
            "global_latency": global_latency,
            "critical_devices_count": critical_devices_count,
            "conclusion": conclusion
        }

        # Gerar PDF
        period_str = f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
        pdf_buffer = generate_sla_pdf(report_data, period_str, stats)
        
        headers = {
            'Content-Disposition': f'attachment; filename="Relatorio_SLA_ISP_{datetime.now().strftime("%Y%m%d")}.pdf"'
        }
        
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except Exception as e:
        print(f"Erro gerando relatório: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF")

@router.get("/incidents/pdf")
async def get_incidents_report_pdf(days: int = 30, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Gera um PDF com o relatório de Incidentes dos últimos X dias.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        start_date = start_date.replace(tzinfo=None)
        
        # Buscar Alertas do período
        stmt = select(Alert).where(Alert.timestamp >= start_date).order_by(Alert.timestamp.desc())
        result = await db.execute(stmt)
        alerts = result.scalars().all()
        
        # --- ESTATÍSTICAS E RESUMO ---
        total_drops = 0
        total_recoveries = 0
        device_issues = {} # {device_id: {name, ip, drops}}
        
        report_data = []
        
        # Buscar todos os equipamentos monitorados para o contador
        eq_res = await db.execute(select(func.count(Equipment.id)).where(Equipment.ip != None))
        total_devices = eq_res.scalar()
        
        for alert in alerts:
            # Processar dados para a tabela
            report_data.append({
                "timestamp": alert.timestamp.strftime('%d/%m/%Y %H:%M'),
                "device_name": alert.device_name,
                "message": alert.message,
                "type": "issue" if "offline" in alert.message.lower() else "info"
            })
            
            # Contabilizar estatísticas
            msg_lower = alert.message.lower()
            is_drop = "offline" in msg_lower or "down" in msg_lower or "queda" in msg_lower
            is_recovery = "online" in msg_lower or "up" in msg_lower or "voltou" in msg_lower
            
            if is_drop:
                total_drops += 1
                
                # Agrupar por dispositivo
                # Nota: Alert tem device_name, precisamos tentar vincular ao IP/ID se possível
                # Assumindo que device_name é único o suficiente para este relatório rápido
                d_name = alert.device_name
                if d_name not in device_issues:
                    device_issues[d_name] = {'name': d_name, 'ip': 'N/A', 'drops': 0}
                device_issues[d_name]['drops'] += 1
                
            elif is_recovery:
                total_recoveries += 1
        
        # Gerar TOP 5 Problemáticos
        sorted_issues = sorted(device_issues.values(), key=lambda x: x['drops'], reverse=True)
        top_problematic = sorted_issues[:5]
        
        # Gerar Conclusão Automática
        conclusion = ""
        if total_drops == 0:
            conclusion = "✅ <b>Excelente estabilidade!</b> Não foram registradas quedas no período analisado. A rede operou com alta confiabilidade."
        else:
            most_issue = top_problematic[0] if top_problematic else None
            conclusion = f"Durante o período, foram registradas <b>{total_drops} interfrupções</b>. "
            
            if most_issue and most_issue['drops'] > 1:
                conclusion += f"A instabilidade concentrou-se principalmente no dispositivo <b>{most_issue['name']}</b>, "
                conclusion += f"que apresentou <b>{most_issue['drops']} quedas</b>. "
                conclusion += "Recomenda-se verificar a alimentação elétrica e o enlace deste equipamento."
            elif len(top_problematic) > 3:
                conclusion += "As quedas ocorreram de forma distribuída em diversos pontos da rede, o que pode indicar instabilidade sistêmica ou falta de energia generalizada."
            else:
                conclusion += "As interrupções foram pontuais e rapidamente recuperadas."

        stats = {
            "total_devices": total_devices,
            "total_drops": total_drops,
            "total_recoveries": total_recoveries,
            "top_problematic": top_problematic,
            "conclusion": conclusion
        }
            
        period_str = f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
        pdf_buffer = generate_incidents_pdf(report_data, period_str, stats)
        
        headers = {
            'Content-Disposition': f'attachment; filename="Relatorio_Executivo_{datetime.now().strftime("%Y%m%d")}.pdf"'
        }
        
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de incidentes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro interno ao gerar PDF")

@router.get("/incidents/recent")
async def get_recent_incidents(limit: int = 50, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Retorna os últimos incidentes registrados.
    """
    stmt = select(Alert).order_by(Alert.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return alerts

@router.get("/incidents/stats")
async def get_incidents_stats(days: int = 7, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Retorna estatísticas consolidadas de incidentes para o dashboard.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    start_date = start_date.replace(tzinfo=None)
    
    # 1. Total Dispositivos
    eq_res = await db.execute(select(func.count(Equipment.id)).where(Equipment.ip != None))
    total_devices = eq_res.scalar()
    
    # 2. Buscar Alertas
    stmt = select(Alert).where(Alert.timestamp >= start_date)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    total_drops = 0
    total_recoveries = 0
    device_issues = {} 
    
    for alert in alerts:
        msg_lower = alert.message.lower()
        is_drop = "offline" in msg_lower or "down" in msg_lower or "queda" in msg_lower
        is_recovery = "online" in msg_lower or "up" in msg_lower or "voltou" in msg_lower
        
        if is_drop:
            total_drops += 1
            d_name = alert.device_name
            if d_name not in device_issues:
                device_issues[d_name] = {'name': d_name, 'drops': 0}
            device_issues[d_name]['drops'] += 1
        elif is_recovery:
            total_recoveries += 1
            
    sorted_issues = sorted(device_issues.values(), key=lambda x: x['drops'], reverse=True)
    top_problematic = sorted_issues[:5]
    
    # Gerar Conclusão
    conclusion = ""
    if total_drops == 0:
        conclusion = "✅ Excelente estabilidade! Nenhuma queda registrada no período."
    else:
        most_issue = top_problematic[0] if top_problematic else None
        conclusion = f"Registradas {total_drops} interrupções. "
        if most_issue and most_issue['drops'] > 1:
            conclusion += f"Maior instabilidade em {most_issue['name']} ({most_issue['drops']} quedas)."
        elif len(top_problematic) > 3:
            conclusion += "Quedas distribuídas na rede."
            
    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_devices": total_devices,
        "total_drops": total_drops,
        "total_recoveries": total_recoveries,
        "top_problematic": top_problematic,
        "conclusion": conclusion
    }

@router.get("/sla/stats")
async def get_sla_stats(days: int = 7, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Retorna estatísticas consolidadas de SLA para o dashboard.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    start_date = start_date.replace(tzinfo=None)
    
    stmt = select(
        PingStatsHourly.device_id,
        func.avg(PingStatsHourly.availability_percent).label('avg_uptime'),
        func.avg(PingStatsHourly.avg_latency_ms).label('avg_latency')
    ).where(
        PingStatsHourly.timestamp >= start_date
    ).group_by(PingStatsHourly.device_id)
    
    stats_result = await db.execute(stmt)
    stats_rows = stats_result.all()
    
    total_uptime = 0
    total_latency = 0
    critical_devices_count = 0
    count = len(stats_rows)
    
    for row in stats_rows:
        up = row.avg_uptime or 0
        lat = row.avg_latency or 0
        total_uptime += up
        total_latency += lat
        
        if up < 99.0:
            critical_devices_count += 1
            
    global_uptime = round(total_uptime / count, 2) if count > 0 else 0
    global_latency = round(total_latency / count, 2) if count > 0 else 0
    
    conclusion = ""
    if global_uptime >= 99.9:
        conclusion = "✅ Excelência Operacional! Rede com estabilidade de classe mundial (>99.9%)."
    elif global_uptime >= 99.0:
        conclusion = "✅ Meta Atingida. Rede operando dentro dos parâmetros de qualidade (>99%)."
    elif global_uptime >= 95.0:
        conclusion = f"⚠️ Atenção. Disponibilidade média ({global_uptime}%) abaixo da meta. {critical_devices_count} dispositivos instáveis."
    else:
        conclusion = f"🚨 Crítico. Problemas severos de disponibilidade ({global_uptime}%). Ação imediata necessária."

    return {
        "global_uptime": global_uptime,
        "global_latency": global_latency,
        "critical_devices_count": critical_devices_count,
        "conclusion": conclusion,
        "monitored_devices": count
    }
