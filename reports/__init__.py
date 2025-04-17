import io
from datetime import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reports.generate_report import get_emotion_report

def create_pdf_report(login_id: str) -> bytes:
    df = get_emotion_report(login_id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("감정 분석 리포트", styles["Title"]))
    elements.append(Paragraph(f"생성일: {datetime.now().date()}", styles["Normal"]))
    
    # 테이블 데이터
    data = [df.columns.tolist()] + df.values.tolist()
    tbl = Table(data)
    elements.append(tbl)

    doc.build(elements)
    return buffer.getvalue()
