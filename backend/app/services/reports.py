from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from backend.app.models import Equipment, PingStatsHourly

def generate_sla_pdf(data: list, period_str: str, stats: dict = None):
    """
    Gera um relatório PDF Executivo de SLA.
    data: List de dicts {name, ip, availability_percent, avg_latency_ms}
    stats: Dict {global_uptime, global_latency, critical_devices_count, conclusion}
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Custom Styles (Same as Incidents)
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1e3a8a'), spaceAfter=20, alignment=1)
    sub_title_style = ParagraphStyle('CustomSubTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#475569'), spaceAfter=15)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1f2937'), leading=14)

    # --- HEADER ---
    elements.append(Paragraph(f"Relatório de Nível de Serviço (SLA)", title_style))
    elements.append(Paragraph(f"ISP Monitor - Análise de Disponibilidade", sub_title_style))
    elements.append(Paragraph(f"<b>Período Analisado:</b> {period_str}", normal_style))
    elements.append(Paragraph(f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.5 * inch))

    # --- 1. RESUMO EXECUTIVO (KPIs) ---
    if stats:
        elements.append(Paragraph("1. Resumo de Performance da Rede", sub_title_style))
        
        avg_up = stats.get('global_uptime', 0)
        up_color = colors.HexColor('#16a34a') if avg_up >= 99 else colors.HexColor('#dc2626')
        
        # KPI Box Table
        kpi_data = [
            [
                f"🌐 Uptime Médio Global\n{avg_up}%",
                f"⚡ Latência Média\n{stats.get('global_latency', 0)} ms", 
                f"🎯 Meta SLA\n99.00%",
                f"⚠️ Dispositivos Críticos\n{stats.get('critical_devices_count', 0)}"
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[1.8*inch]*4)
        kpi_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, 0), up_color), # Colorize Uptime
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#334155')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]), 
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.3 * inch))

    # --- 2. LISTAGEM DE DISPOSITIVOS ---
    elements.append(Paragraph("2. Detalhamento por Dispositivo", sub_title_style))
    
    table_data = [['Dispositivo', 'IP', 'Disponibilidade (%)', 'Latência (ms)']]
    
    for item in data:
        uptime = item.get('availability_percent', 0)
        name = item.get('name', 'N/A')
        ip = item.get('ip', 'N/A')
        lat = f"{item.get('avg_latency_ms', 0)} ms"
        
        # Colorize logic for uptime text
        # We can't easily colorize just text in simple Table without Paragraph, 
        # so lets use background color for row if critical
        row = [name, ip, f"{uptime}%", lat]
        table_data.append(row)

    t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
    ]))
    
    # Conditional formatting for critical rows (< 99%)
    for i, item in enumerate(data):
        if item.get('availability_percent', 0) < 99.0:
            # Row index is i + 1 because of header
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (2, i+1), (2, i+1), colors.red), # Highlight Uptime column text
                ('FONTNAME', (0, i+1), (-1, i+1), 'Helvetica-BoldOblique'), # Italic specific row
            ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.4 * inch))
    
    # --- 3. CONCLUSÃO AUTOMÁTICA ---
    if stats and stats.get('conclusion'):
        elements.append(Paragraph("3. Conclusão da Análise de Nível de Serviço", sub_title_style))
        
        conclusion_style = ParagraphStyle(
            'Conclusion',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            backColor=colors.HexColor('#f0f9ff'),
            borderColor=colors.HexColor('#0ea5e9'),
            borderPadding=15,
            borderWidth=1,
            borderRadius=8
        )
        elements.append(Paragraph(stats.get('conclusion'), conclusion_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_incidents_pdf(data: list, period_str: str, stats: dict = None):
    """
    Gera um relatório PDF Executivo de Incidentes.
    data: List de dicts com {timestamp, device_name, message, type}
    stats: Dict com estatísticas consolidadas {total_devices, total_drops, total_recoveries, top_problematic, conclusion}
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'), # Blue 900
        spaceAfter=20,
        alignment=1
    )
    
    sub_title_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#475569'), # Slate 600
        spaceAfter=15
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        leading=14
    )

    # --- HEADER ---
    elements.append(Paragraph(f"Relatório Executivo de Rede", title_style))
    elements.append(Paragraph(f"ISP Monitor - Análise de Incidentes", sub_title_style))
    elements.append(Paragraph(f"<b>Período Analisado:</b> {period_str}", normal_style))
    elements.append(Paragraph(f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.5 * inch))

    # --- 1. RESUMO EXECUTIVO (KPIs) ---
    if stats:
        elements.append(Paragraph("1. Resumo do Período", sub_title_style))
        
        # KPI Box Table
        kpi_data = [
            [
                f"📡 Monitorados\n{stats.get('total_devices', 0)}",
                f"⬇️ Quedas\n{stats.get('total_drops', 0)}", 
                f"🔁 Recuperações\n{stats.get('total_recoveries', 0)}",
                f"⚠️ Instáveis\n{len(stats.get('top_problematic', []))}"
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[1.8*inch]*4)
        kpi_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f1f5f9')), # Slate 100
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#fee2e2')), # Red 100
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#dcfce7')), # Green 100
            ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#ffedd5')), # Orange 100
            ('BOX', (0, 0), (-1, -1), 1, colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]), 
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.3 * inch))

        # --- 2. RANKING DE QUEDAS (Top 5) ---
        if stats.get('top_problematic'):
            elements.append(Paragraph("2. Dispositivos com Maior Instabilidade (Top 5)", sub_title_style))
            
            rank_data = [['Dispositivo', 'IP', 'Quedas (Offline)', 'Estabilidade']]
            
            for item in stats.get('top_problematic', []):
                rank_data.append([
                    item.get('name', 'N/A'),
                    item.get('ip', 'N/A'),
                    str(item.get('drops', 0)),
                    "Crítico" if item.get('drops', 0) > 10 else "Atenção"
                ])
                
            rank_table = Table(rank_data, colWidths=[2.5*inch, 2.0*inch, 1.5*inch, 1.2*inch])
            rank_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')), # Header Gray
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]) # Striped
            ]))
            elements.append(rank_table)
            elements.append(Spacer(1, 0.4 * inch))

    # --- 3. LISTA DE EVENTOS (Logs) ---
    elements.append(Paragraph("3. Detalhamento de Eventos Recentes", sub_title_style))
    
    event_table_data = [['Data/Hora', 'Equipamento', 'Evento / Status']]
    
    # Limitar aos últimos 100 eventos para não explodir o PDF se tiver muitos
    recent_events = data[:200]
    
    for item in recent_events:
        msg = item.get('message', 'N/A')
        
        # Simple icon logic
        if "Offline" in msg or "down" in msg or "Queda" in msg:
            status_icon = "🔴 Queda"
            bg_color = colors.HexColor('#fef2f2') # Red 50
        elif "Online" in msg or "up" in msg or "Voltou" in msg:
            status_icon = "🟢 Voltou"
            bg_color = colors.HexColor('#f0fdf4') # Green 50
        else:
            status_icon = "ℹ️ Info"
            bg_color = colors.white
            
        event_table_data.append([
            item.get('timestamp', 'N/A'),
            item.get('device_name', 'N/A'),
            f"{status_icon} - {msg}"
        ])

    t = Table(event_table_data, colWidths=[1.5*inch, 2.0*inch, 3.7*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Header Blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.4 * inch))
    
    # --- 4. CONCLUSÃO AUTOMÁTICA ---
    if stats and stats.get('conclusion'):
        elements.append(Paragraph("4. Conclusão da Análise", sub_title_style))
        
        conclusion_style = ParagraphStyle(
            'Conclusion',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            backColor=colors.HexColor('#f0f9ff'),
            borderColor=colors.HexColor('#0ea5e9'),
            borderPadding=15,
            borderWidth=1,
            borderRadius=8
        )
        
        elements.append(Paragraph(stats.get('conclusion'), conclusion_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
