from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from backend.app.models import Equipment, PingStatsHourly

def generate_sla_pdf(data: list, period_str: str):
    """
    Gera um relatório PDF simples de SLA (Service Level Agreement).
    data: List de dicts ou objetos com {name, ip, uptime, latency}
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    # Title
    elements.append(Paragraph(f"Relatório de Disponibilidade (SLA)", title_style))
    elements.append(Paragraph(f"Período: {period_str}", styles['Normal']))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Table Header
    table_data = [['Dispositivo', 'IP', 'Disponibilidade (%)', 'Latência Média (ms)']]
    
    # Table Rows
    online_count = 0
    total_count = len(data) if data else 0
    
    for item in data:
        # Define cor baseada no SLA
        uptime = item.get('availability_percent', 0)
        
        # Style
        name = item.get('name', 'N/A')
        ip = item.get('ip', 'N/A')
        lat = f"{item.get('avg_latency_ms', 0)} ms"
        
        row = [name, ip, f"{uptime}%", lat]
        table_data.append(row)
        
        if uptime > 99: online_count += 1

    # Create Table
    t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Resumo
    summary_text = f"<b>Resumo Geral:</b><br/>Total de Dispositivos: {total_count}<br/>Dispositivos com SLA > 99%: {online_count}"
    elements.append(Paragraph(summary_text, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
