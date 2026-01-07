from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from backend.app.models import Equipment, PingStatsHourly

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker

def generate_sla_pdf(data: list, period_str: str, stats: dict = None):
    # ... (código existente de setup) ...
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    # ... styles ...
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

        # --- GRÁFICOS ---
        # PIE CHART (Distribution)
        if stats.get('pie_data') and sum(stats['pie_data']) > 0:
            elements.append(Paragraph("Distribuição de Qualidade (Dispositivos)", normal_style))
            elements.append(Spacer(1, 10))
            
            d = Drawing(450, 200)
            pc = Pie()
            pc.x = 100
            pc.y = 20
            pc.width = 150
            pc.height = 150
            pc.data = stats['pie_data']
            # Labels only if val > 0
            pc.labels = [str(v) if v > 0 else '' for v in pc.data]
            
            pc.slices.strokeWidth = 1
            pc.slices.strokeColor = colors.white
            pc.slices[0].fillColor = colors.HexColor('#166534') # Excellent (Dark Green)
            pc.slices[1].fillColor = colors.HexColor('#22c55e') # Good (Green)
            pc.slices[2].fillColor = colors.HexColor('#f59e0b') # Warning (Amber)
            pc.slices[3].fillColor = colors.HexColor('#ef4444') # Critical (Red)
            
            d.add(pc)
            
            legend = Legend()
            legend.x = 300
            legend.y = 150
            legend.dx = 10
            legend.dy = 10
            legend.fontName = 'Helvetica'
            legend.fontSize = 10
            legend.boxAnchor = 'nw'
            legend.columnMaximum = 10
            legend.strokeWidth = 0
            legend.alignment = 'right'
            legend.colorNamePairs = [
                (colors.HexColor('#166534'), '> 99.9% (Excepcional)'),
                (colors.HexColor('#22c55e'), '99.0% - 99.9% (Bom)'),
                (colors.HexColor('#f59e0b'), '95.0% - 99.0% (Atenção)'),
                (colors.HexColor('#ef4444'), '< 95.0% (Crítico)')
            ]
            d.add(legend)
            elements.append(d)
            elements.append(Spacer(1, 0.2 * inch))

        # LINE CHART (Trends)
        if stats.get('line_data') and len(stats['line_data']) > 1:
            elements.append(Paragraph("Evolução Diária da Disponibilidade (%)", normal_style))
            elements.append(Spacer(1, 10))
            
            d_line = Drawing(450, 180)
            lc = HorizontalLineChart()
            lc.x = 30
            lc.y = 30
            lc.height = 120
            lc.width = 380
            
            line_raw_data = stats['line_data'] # [(date, val)]
            # Limit to last 15 points to fit if too many
            if len(line_raw_data) > 20:
                 # Take every Nth point to fit? Or just last 15?
                 # Let's take last 15 for clarity
                 line_raw_data = line_raw_data[-15:]
            
            dates = [x[0] for x in line_raw_data]
            vals = [x[1] for x in line_raw_data]
            
            lc.data = [vals]
            lc.categoryAxis.categoryNames = dates
            lc.categoryAxis.labels.boxAnchor = 'n'
            lc.categoryAxis.labels.angle = 45
            lc.categoryAxis.labels.dy = -10
            lc.categoryAxis.labels.fontSize = 8
            
            min_val = min(vals)
            lc.valueAxis.valueMin = max(0, min_val - 2) if min_val > 90 else 0
            lc.valueAxis.valueMax = 100.5
            
            lc.lines[0].strokeColor = colors.HexColor('#2563eb')
            lc.lines[0].symbol = makeMarker('Circle')
            lc.lines[0].symbol.size = 4
            lc.lines[0].symbol.fillColor = colors.white
            lc.lines[0].symbol.strokeColor = colors.HexColor('#2563eb')
            
            d_line.add(lc)
            elements.append(d_line)
            elements.append(Spacer(1, 0.4 * inch))

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

    # --- 3. SUMÁRIO DE EVENTOS POR EQUIPAMENTO (Groups logs by device) ---
    elements.append(Paragraph("3. Resumo de Eventos por Equipamento", sub_title_style))
    
    event_table_data = [['Período', 'Equipamento', 'Status do Período']]
    
    # Pre-calculate counts and date ranges per device
    device_summary = {}
    for ev in data:
        d_name = ev.get('device_name', 'Unknown')
        ts_str = ev.get('timestamp', '')
        
        if d_name not in device_summary:
            device_summary[d_name] = {
                'down': 0, 'up': 0, 
                'first': ts_str, 'last': ts_str
            }
        
        # Update counters
        m_txt = ev.get('message', '').lower()
        if any(x in m_txt for x in ["offline", "down", "queda", "falha"]):
             device_summary[d_name]['down'] += 1
        elif any(x in m_txt for x in ["online", "up", "voltou", "restabelecida"]):
             device_summary[d_name]['up'] += 1
             
        # Update range (Assuming data is mostly chronological, but we check anyway)
        # Simply keeping track of seen timestamps
        if ts_str < device_summary[d_name]['first']: device_summary[d_name]['first'] = ts_str
        if ts_str > device_summary[d_name]['last']: device_summary[d_name]['last'] = ts_str

    # Build the table rows from grouped data
    for d_name, info in device_summary.items():
        # Format Period: dd/mm/yyyy ao dd/mm/yyyy
        # Extract only date part if it's "dd/mm/yyyy HH:MM"
        d1 = info['first'].split(' ')[0] if ' ' in info['first'] else info['first']
        d2 = info['last'].split(' ')[0] if ' ' in info['last'] else info['last']
        period_text = f"{d1} ao {d2}"
        
        # Format Status: Quedas: X | Voltas: Y
        status_text = f"Quedas: {info['down']} | Voltas: {info['up']}"
        
        event_table_data.append([
            period_text,
            d_name,
            Paragraph(status_text, normal_style)
        ])

    # If no data
    if len(event_table_data) == 1:
        event_table_data.append(["-", "Nenhum evento registrado", "-"])

    t = Table(event_table_data, colWidths=[2.2*inch, 2.3*inch, 2.7*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Header Blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
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
