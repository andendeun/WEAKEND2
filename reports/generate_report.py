import io
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# 한글폰트로 나눔고딕 사용 (Streamlit Cloud에 APT로 설치된 경로)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Ubuntu 스트림릿 컨테이너 기준 경로
SYSTEM_FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
if not os.path.isfile(SYSTEM_FONT):
    raise FileNotFoundError(f"나눔고딕 폰트를 찾을 수 없습니다: {SYSTEM_FONT}")
pdfmetrics.registerFont(TTFont("NanumGothic", SYSTEM_FONT))


def get_emotion_report(login_id: str) -> pd.DataFrame:
    """
    login_id로 users → chat_log → emotions → middle_categories를 조회해,
    DataFrame(columns=['분석 날짜','감정 카테고리','감정 확신도'])로 반환합니다.
    """
    # 1) .env에서 Supabase 정보 로드
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 2) login_id로 userid 조회
    res = supabase.table("users") \
                  .select("userid") \
                  .eq("login_id", login_id) \
                  .single() \
                  .execute()
    if not res.data:
        return pd.DataFrame()
    user_id = res.data["userid"]

    # 3) 해당 userid의 chat_log → chat_id 리스트
    logs = supabase.table("chat_log") \
                   .select("chat_id") \
                   .eq("userid", user_id) \
                   .execute().data or []
    chat_ids = [r["chat_id"] for r in logs]
    if not chat_ids:
        return pd.DataFrame()

    # 4) emotions 테이블 조회
    em = supabase.table("emotions") \
                 .select("analysis_date, emotion_score, middle_category_id") \
                 .in_("chat_id", chat_ids) \
                 .order("analysis_date", desc=False) \
                 .execute().data or []
    df = pd.DataFrame(em)
    if df.empty:
        return df

    # 5) 날짜 형 변환
    df["analysis_date"] = pd.to_datetime(df["analysis_date"]).dt.date

    # 6) middle_categories에서 매핑 정보 조회
    cats = supabase.table("middle_categories") \
                   .select("middle_category_id, middle_categoryname") \
                   .execute().data or []
    cat_df = pd.DataFrame(cats)

    # 7) merge 및 컬럼 재정리
    df = df.merge(cat_df, on="middle_category_id", how="left")
    df = df[["analysis_date", "middle_categoryname", "emotion_score"]]
    df.columns = ["분석 날짜", "감정 카테고리", "감정 확신도"]

    return df





def create_pdf_report(login_id: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 데이터 로드
    from reports.emotion_trend_plot import load_data
    df = load_data(login_id)

    # Title 페이지
    pdf.setFont("NotoSansKR", 24)  
    pdf.drawCentredString(width/2, height-80, f"{login_id}님의 감정 리포트")
    pdf.setFont("NotoSansKR", 12)
    pdf.drawString(50, height-110, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    pdf.showPage()

    # PDF에 삽입할 Figure들을 동적으로 import
    from reports.emotion_trend_plot import (
        build_dashboard_fig,
        build_trend_fig,
        build_calendar_fig,
        build_alert_fig,
    )
    figs = [
        build_dashboard_fig(df),
        build_trend_fig(df),
        build_calendar_fig(df),
        build_alert_fig(df),
    ]

    for fig in figs:
        # 1) Plotly Figure → PNG → ImageReader
        img_bytes = fig.to_image(format="png", engine="kaleido")
        img = ImageReader(io.BytesIO(img_bytes))

        # 실제 PNG 크기로 비율 계산
        orig_w, orig_h = img.getSize()
        aspect = orig_h / orig_w

        max_w, max_h = width - 100, height - 100
        w = max_w
        h = w * aspect
        if h > max_h:
            h = max_h
            w = h / aspect

        # 5) 중앙 정렬 삽입 좌표
        x = (width - w) / 2
        y = (height - h) / 2

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()