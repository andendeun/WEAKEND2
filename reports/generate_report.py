# reports/generate_report.py

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reports.emotion_trend_plot import (
    load_data,
    build_dashboard_fig,
    build_trend_fig,
    build_calendar_fig,
    build_alert_fig,
)

def create_pdf_report(login_id: str) -> bytes:
    """
    Streamlit 화면용 Plotly Figure들을 A4 PDF에 페이지별로 삽입해서
    바이트로 반환합니다.
    """
    # 1) 데이터 로드
    df = load_data(login_id)
    buffer = io.BytesIO()

    # 2) PDF 캔버스 세팅 (A4)
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4  # (595.27pt, 841.89pt)

    # 3) Title 페이지
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width/2, height-80, f"{login_id}님의 감정 리포트")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height-110, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    pdf.showPage()

    # 4) 그릴 Figure 목록
    figs = [
        build_dashboard_fig(df),
        build_trend_fig(df),
        build_calendar_fig(df),
        build_alert_fig(df),
    ]

    # 5) 각 Figure를 PNG로 변환 → PDF에 삽입
    for fig in figs:
        # Plotly Figure → PNG bytes (kaleido 필요)
        img_bytes = fig.to_image(format="png", engine="kaleido")
        img = ImageReader(io.BytesIO(img_bytes))

        # 이미지 크기 계산 (A4에 맞추되, 여백 50pt)
        max_width  = width  - 100
        max_height = height - 100
        aspect = fig.layout.height / fig.layout.width
        draw_width  = max_width
        draw_height = max_width * aspect
        if draw_height > max_height:
            draw_height = max_height
            draw_width  = max_height / aspect

        # 중앙 정렬
        x = (width  - draw_width)  / 2
        y = (height - draw_height) / 2

        pdf.drawImage(img, x, y, width=draw_width, height=draw_height, mask='auto')
        pdf.showPage()

    # 6) PDF 저장 후 반환
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
