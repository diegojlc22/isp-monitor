from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from backend.app.models import Equipment, PingStatsHourly

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker

# --- CUSTOM DESIGN & LAYOUT ---
# Cores da Marca (Inspirado no Dashboard)
COLOR_PRIMARY = colors.HexColor('#1e40af') # Blue 800
COLOR_SECONDARY = colors.HexColor('#3b82f6') # Blue 500
COLOR_BG = colors.HexColor('#f8fafc') # Slate 50
COLOR_TEXT = colors.HexColor('#1e293b') # Slate 800
COLOR_ACCENT = colors.HexColor('#0ea5e9') # Sky 500

def create_header(canvas, doc):
    canvas.saveState()
    
    # 1. Header Bar
    width, height = A4
    header_height = 80
    
    # Background Bar (Gradient-like effect using solid blocks)
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(0, height - header_height, width, header_height, fill=True, stroke=False)
    
    # Border Line
    canvas.setStrokeColor(colors.white)
    canvas.setLineWidth(1)
    canvas.line(0, height - header_height, width, height - header_height)

    # 2. Logo / Brand Name
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 22)
    canvas.drawString(40, height - 50, "ISP MONITOR")
    
    canvas.setFont('Helvetica', 10)
    canvas.drawString(40, height - 68, "Relatório de Inteligência de Rede")

    # 3. Date / Confidential Label
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(width - 40, height - 40, "CONFIDENCIAL")
    
    canvas.setFont('Helvetica', 9)
    date_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    canvas.drawRightString(width - 40, height - 55, f"Gerado em: {date_str}")
    
    canvas.restoreState()

def create_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    
    # Footer Line
    canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
    canvas.setLineWidth(0.5)
    canvas.line(40, 50, width - 40, 50)
    
    # Page Number
    page_num = canvas.getPageNumber()
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(width - 40, 35, f"Página {page_num}")
    
    # Brand Footer
    canvas.drawString(40, 35, "ISP Monitor - Sistema de Gestão de Provedores")
    canvas.setFont('Helvetica-Oblique', 8)
    canvas.drawCentredString(width/2.0, 35, "Uso exclusivo interno")
    
    canvas.restoreState()

def get_base_styles():
    styles = getSampleStyleSheet()
    
    # Título da Seção
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=COLOR_PRIMARY,
        spaceBefore=20,
        spaceAfter=15,
        fontName='Helvetica-Bold'
    ))
    
    # Subtítulo (para gráficos)
    styles.add(ParagraphStyle(
        name='ChartTitle',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        spaceBefore=10,
        spaceAfter=5,
        fontName='Helvetica-Bold'
    ))

    # Texto Normal Customizado
    styles.add(ParagraphStyle(
        name='ReportText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=COLOR_TEXT,
        alignment=TA_LEFT
    ))
    
    # Box de Conclusão / Insights
    styles.add(ParagraphStyle(
        name='InsightBox',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f0f9ff'),
        borderColor=COLOR_ACCENT,
        borderWidth=1,
        borderPadding=15,
        borderRadius=5,
        spaceBefore=10,
        spaceAfter=10
    ))
    
    return styles

def generate_sla_pdf(data: list, period_str: str, stats: dict = None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=100, bottomMargin=60)
    
    styles = get_base_styles()
    elements = []
    
    # --- CAPA / SUMÁRIO (Simplificado para Executive Summary na primeira página) ---
    # Título do Relatório
    elements.append(Paragraph("Análise de Nível de Serviço (SLA)", 
                             ParagraphStyle('MainTitle', parent=styles['Heading1'], fontSize=28, textColor=COLOR_PRIMARY, spaceAfter=5)))
    
    elements.append(Paragraph(f"Período de Análise: {period_str}", 
                             ParagraphStyle('SubMain', parent=styles['Normal'], fontSize=12, textColor=colors.gray, spaceAfter=20)))
    
    elements.append(Spacer(1, 0.2*inch))

    # --- 1. CARDS DE KPI (Tabela Visual) ---
    if stats:
        # Preparar dados dos Cards
        avg_up = stats.get('global_uptime', 0)
        up_color = colors.HexColor('#166534') if avg_up >= 99 else (colors.HexColor('#ca8a04') if avg_up >= 95 else colors.HexColor('#dc2626'))
        
        # Símbolos manuais (ReportLab não suporta emojis direto em todas as fontes padrão, usando caracteres simples ou imagens seria melhor)
        # Vamos usar texto simples formatado
        
        # Design em Grid 2x2
        kpi_data = [
            [
                f"DISPONIBILIDADE\nAvg: {avg_up}%",
                f"LATÊNCIA\nAvg: {stats.get('global_latency', 0)} ms"
            ],
            [
                f"META SLA\nTarget: 99.00%",
                f"CRÍTICOS\nDevices: {stats.get('critical_devices_count', 0)}"
            ]
        ]
        
        # Estilo dos Cards (Tabela com células coloridas)
        t_kpi = Table(kpi_data, colWidths=[3.2*inch, 3.2*inch], rowHeights=[0.8*inch, 0.8*inch])
        t_kpi.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (0, 0), up_color), # Uptime Color
            ('TEXTCOLOR', (1, 0), (-1, -1), COLOR_SECONDARY), # Others Blue
            ('TEXTCOLOR', (1, 1), (1, 1), colors.red if stats.get('critical_devices_count', 0) > 0 else colors.gray),
            
            # Espaçamento e Bordas Fantasma (Grid Gap simulado com Padding)
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#f0fdf4') if avg_up >= 99 else colors.HexColor('#fef2f2')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#f0f9ff')),
            ('BACKGROUND', (0,1), (0,1), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (1,1), (1,1), colors.HexColor('#fff7ed') if stats.get('critical_devices_count', 0) > 0 else colors.HexColor('#f8fafc')),
            
            ('ROUNDEDCORNERS', [8, 8, 8, 8]), 
            ('GRID', (0,0), (-1,-1), 4, colors.white), # White thick grid to simulate gap
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 0.4*inch))

        # --- 2. GRÁFICOS VISUAIS ---
        elements.append(Paragraph("Diagnóstico Visual da Rede", styles['SectionTitle']))
        
        # Layout Lado a Lado (Pie Chart + Line Chart) se houver espaço, senão um abaixo do outro
        # Vamos colocar um abaixo do outro para clareza no PDF A4
        
        # A) DISTRIBUIÇÃO (PIE)
        if stats.get('pie_data') and sum(stats['pie_data']) > 0:
            elements.append(Paragraph("Distribuição de Saúde dos Ativos", styles['ChartTitle']))
            
            d = Drawing(400, 150)
            pc = Pie()
            pc.x = 80
            pc.y = 10
            pc.width = 130
            pc.height = 130
            pc.data = stats['pie_data']
            pc.labels = [f"{v}" if v > 0 else "" for v in pc.data]
            pc.sideLabels = 1 # Labels inside if fit
            
            # Colors
            pc.slices[0].fillColor = colors.HexColor('#16a34a') # Exc
            pc.slices[1].fillColor = colors.HexColor('#4ade80') # Good
            pc.slices[2].fillColor = colors.HexColor('#facc15') # Warn
            pc.slices[3].fillColor = colors.HexColor('#ef4444') # Crit
            
            d.add(pc)
            
            # Legend
            legend = Legend()
            legend.x = 250
            legend.y = 120
            legend.dx = 8
            legend.dy = 8
            legend.fontName = 'Helvetica'
            legend.fontSize = 9
            legend.boxAnchor = 'nw'
            legend.columnMaximum = 10
            legend.colorNamePairs = [
                (colors.HexColor('#16a34a'), 'Excelente (>99.9%)'),
                (colors.HexColor('#4ade80'), 'Bom (99.0-99.9%)'),
                (colors.HexColor('#facc15'), 'Atenção (95-99%)'),
                (colors.HexColor('#ef4444'), 'Crítico (<95%)')
            ]
            d.add(legend)
            elements.append(d)
            elements.append(Spacer(1, 0.2*inch))

        # B) EVOLUÇÃO (LINE)
        if stats.get('line_data') and len(stats['line_data']) > 1:
            elements.append(Paragraph("Tendência de Disponibilidade (Últimos Dias)", styles['ChartTitle']))
            
            d_line = Drawing(450, 160)
            lc = HorizontalLineChart()
            lc.x = 30
            lc.y = 20
            lc.height = 120
            lc.width = 400
            
            # Data
            line_raw = stats['line_data']
            # Amostrar se muito longo
            if len(line_raw) > 15: line_raw = line_raw[-15:]
            
            dates = [x[0] for x in line_raw]
            vals = [x[1] for x in line_raw]
            
            lc.data = [vals]
            lc.categoryAxis.categoryNames = dates
            lc.categoryAxis.labels.angle = 45
            lc.categoryAxis.labels.boxAnchor = 'ne'
            lc.categoryAxis.labels.dx = 0
            lc.categoryAxis.labels.dy = -5
            lc.categoryAxis.labels.fontName = 'Helvetica'
            lc.categoryAxis.labels.fontSize = 8
            
            # Y Axis
            min_v = min(vals)
            lc.valueAxis.valueMin = max(80, min_v - 5) 
            lc.valueAxis.valueMax = 100.2
            lc.valueAxis.gridStrokeWidth = 0.5
            lc.valueAxis.gridStrokeColor = colors.HexColor('#e2e8f0')
            lc.valueAxis.visibleGrid = 1
            
            lc.lines[0].strokeColor = COLOR_SECONDARY
            lc.lines[0].strokeWidth = 2
            
            d_line.add(lc)
            elements.append(d_line)
            elements.append(Spacer(1, 0.4*inch))

    # --- 3. TABELA DETALHADA ---
    elements.append(PageBreak()) # Nova página para tabela
    elements.append(Paragraph("Detalhamento Técnico por Ativo", styles['SectionTitle']))
    
    # Table Header
    table_data = [['DISPOSITIVO', 'ENDEREÇO IP', 'UPTIME', 'LATÊNCIA']]
    
    # Table Rows
    for item in data:
        up_val = item.get('availability_percent', 0)
        row = [
            item.get('name', 'N/A')[:30], # Truncate name
            item.get('ip', 'N/A'),
            f"{up_val}%",
            f"{item.get('avg_latency_ms', 0)} ms"
        ]
        table_data.append(row)
        
    # Table Style
    t = Table(table_data, colWidths=[3.0*inch, 1.5*inch, 1.2*inch, 1.2*inch], repeatRows=1)
    
    # Base Style
    tbl_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Data Rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'), # Center stats
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    
    # Conditional Formatting Loop
    for i, item in enumerate(data):
        if item.get('availability_percent', 0) < 99.0:
            row_idx = i + 1
            tbl_style.append(('TEXTCOLOR', (2, row_idx), (2, row_idx), colors.red))
            tbl_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            
    t.setStyle(TableStyle(tbl_style))
    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))
    
    # --- 4. CONCLUSÃO ---
    if stats and stats.get('conclusion'):
         elements.append(Paragraph("Parecer Técnico", styles['SectionTitle']))
         elements.append(Paragraph(stats.get('conclusion'), styles['InsightBox']))

    # Build PDF with Header/Footer
    doc.build(elements, onFirstPage=create_header, onLaterPages=create_header)
    # Note: create_header actually draws both Header and calls helper for Footer? 
    # Let's adjust create_header to do both or add footer explicitly.
    # The standard way is onFirstPage/onLaterPages. I will update create_header to call create_footer.
    
    buffer.seek(0)
    return buffer

def generate_incidents_pdf(data: list, period_str: str, stats: dict = None):
    # Reuse similar professional style
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=100, bottomMargin=60)
    
    styles = get_base_styles()
    elements = []
    
    # Title
    elements.append(Paragraph("Relatório Executivo de Incidentes", 
                             ParagraphStyle('MainTitle', parent=styles['Heading1'], fontSize=26, textColor=COLOR_PRIMARY, spaceAfter=5)))
    elements.append(Paragraph(f"Monitoramento de Estabilidade e Auditoria de Falhas", 
                             ParagraphStyle('SubMain', parent=styles['Normal'], fontSize=12, textColor=colors.gray, spaceAfter=20)))
    elements.append(Paragraph(f"Período: {period_str}", 
                             ParagraphStyle('SubMain2', parent=styles['Normal'], fontSize=10, textColor=COLOR_TEXT)))
    elements.append(Spacer(1, 0.3*inch))

    # --- 1. KPI CARDS ---
    if stats:
        # Data
        drops = stats.get('total_drops', 0)
        recs = stats.get('total_recoveries', 0)
        unstable = len(stats.get('top_problematic', []))
        
        kpi_data = [
            [
                f"TOTAL DE QUEDAS\nEventos: {drops}",
                f"RECUPERAÇÕES\nAuto: {recs}",
                f"PONTOS INSTÁVEIS\nDevices: {unstable}"
            ]
        ]
        
        t_kpi = Table(kpi_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch], rowHeights=[0.8*inch])
        t_kpi.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#ef4444') if drops > 0 else colors.HexColor('#166534')),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#16a34a')),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#f59e0b')),
            
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#fef2f2')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f0fdf4')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#fffbeb')),
            
            ('ROUNDEDCORNERS', [6, 6, 6, 6],),
            ('GRID', (0,0), (-1,-1), 4, colors.white),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 0.4*inch))
        
        # --- 2. GRÁFICOS ---
        elements.append(Paragraph("Análise Visual de Estabilidade", styles['SectionTitle']))
        
        # A) Timeline (Vertical Bar) for Daily Incidents
        if stats.get('daily_evolution') and len(stats['daily_evolution']) > 1:
            elements.append(Paragraph("Histórico Diário de Falhas", styles['ChartTitle']))
            
            evo_data = stats['daily_evolution']
            if len(evo_data) > 15: evo_data = evo_data[-15:]
            
            dates = [x[0] for x in evo_data]
            vals = [x[1] for x in evo_data]
            
            d_evo = Drawing(400, 160)
            bc = VerticalBarChart()
            bc.x = 40
            bc.y = 20
            bc.height = 120
            bc.width = 380
            bc.data = [vals]
            bc.categoryAxis.categoryNames = dates
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(vals) + 2 if vals else 5
            
            bc.bars[0].fillColor = colors.HexColor('#ef4444') # Red bars
            
            d_evo.add(bc)
            elements.append(d_evo)
            elements.append(Spacer(1, 0.2*inch))
            
        # B) Top Offenders (Horizontal Bar)
        if stats.get('top_problematic'):
            elements.append(Paragraph("Top 5 - Ofensores de Rede", styles['ChartTitle']))
            
            items = stats['top_problematic'][:5]
            names = [i.get('name', 'N/A')[:15] for i in items]
            vals = [i.get('drops', 0) for i in items]
            
            d_top = Drawing(400, 160)
            hc = HorizontalBarChart()
            hc.x = 80
            hc.y = 20
            hc.height = 130
            hc.width = 300
            hc.data = [vals]
            hc.categoryAxis.categoryNames = names
            hc.valueAxis.valueMin = 0
            hc.valueAxis.valueMax = max(vals) + 2 if vals else 5
            
            hc.bars[0].fillColor = colors.HexColor('#dc2626') # Dark Red
            
            d_top.add(hc)
            elements.append(d_top)
            elements.append(Spacer(1, 0.4*inch))

    # --- 3. TABELA DE EVENTOS ---
    elements.append(PageBreak())
    elements.append(Paragraph("Registro de Eventos por Equipamento", styles['SectionTitle']))
    
    event_table_data = [['PERÍODO', 'EQUIPAMENTO', 'RESUMO DE STATUS']]
    
    # Logic reuse
    device_summary = {}
    for ev in data:
        d_name = ev.get('device_name', 'Unknown')
        ts_str = ev.get('timestamp', '')
        if d_name not in device_summary:
            device_summary[d_name] = {'down': 0, 'up': 0, 'first': ts_str, 'last': ts_str}
        
        m_txt = ev.get('message', '').lower()
        if any(x in m_txt for x in ["offline", "down", "queda"]): device_summary[d_name]['down'] += 1
        elif any(x in m_txt for x in ["online", "up", "voltou"]): device_summary[d_name]['up'] += 1
        
        if ts_str < device_summary[d_name]['first']: device_summary[d_name]['first'] = ts_str
        if ts_str > device_summary[d_name]['last']: device_summary[d_name]['last'] = ts_str

    for d_name, info in device_summary.items():
        d1 = info['first'].split(' ')[0] if ' ' in info['first'] else info['first']
        d2 = info['last'].split(' ')[0] if ' ' in info['last'] else info['last']
        period_text = f"{d1} até {d2}"
        status_text = f"Quedas: {info['down']} | Retornos: {info['up']}"
        
        event_table_data.append([
            period_text, 
            d_name, 
            Paragraph(status_text, styles['ReportText'])
        ])

    if len(event_table_data) == 1:
        event_table_data.append(["-", "Sem eventos registrados", "-"])

    t = Table(event_table_data, colWidths=[2.0*inch, 2.5*inch, 2.5*inch], repeatRows=1)
    
    tbl_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]
    t.setStyle(TableStyle(tbl_style))
    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))

    # --- 4. CONCLUSÃO ---
    if stats and stats.get('conclusion'):
         elements.append(Paragraph("Conclusão Executiva", styles['SectionTitle']))
         elements.append(Paragraph(stats.get('conclusion'), styles['InsightBox']))

    # Wrapper for Header+Footer
    def draw_page_template(canvas, doc):
        create_header(canvas, doc)
        create_footer(canvas, doc)

    doc.build(elements, onFirstPage=draw_page_template, onLaterPages=draw_page_template)
    buffer.seek(0)
    return buffer
