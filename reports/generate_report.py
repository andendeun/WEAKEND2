# reports/generate_report.py

import os
import io
from datetime import datetime
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def get_emotion_report(login_id: str) -> pd.DataFrame:
    """
    login_id로 users → chat_log → emotions를 조회해,
    DataFrame(컬럼: 분석 날짜, 감정 카테고리, 감정 확신도)으로 반환합니다.
    """
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1) userid 조회
    user_res = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single().execute()
    if not user_res.data:
        return pd.DataFrame()
    user_id = user_res.data["userid"]

    # 2) chat_log → chat_id 리스트
    logs = supabase.table("chat_log") \
        .select("chat_id") \
        .eq("userid", user_id) \
        .execute().data or []
    chat_ids = [r["chat_id"] for r in logs]
    if not chat_ids:
        return pd.DataFrame()

    # 3) emotions 테이블 조회
    em = supabase.table("emotions") \
        .select("analysis_date, emotion_score, middle_category_id") \
        .in_("chat_id", chat_ids) \
        .order("analysis_date", desc=False) \
        .execute().data or []
    df = pd.DataFrame(em)
    if df.empty:
        return df

    # 4) 날짜 및 카테고리명 매핑
    df["analysis_date"] = pd.to_datetime(df["analysis_date"]).dt.date
    cat = supabase.table("middle_categories") \
        .select("middle_category_id, middle_categoryname") \
        .execute().data or []
    cat_df = pd.DataFrame(cat)
    df = df.merge(cat_df, on="middle_category_id", how="left")

    # 5) 컬럼 정리
    df = df[["analysis_date", "middle_categoryname", "emotion_score"]]
    df.columns = ["분석 날짜", "감정 카테고리", "감정 확신도"]
    return df

def create_pdf_report(login_id: str) -> bytes:
    """
    get_emotion_report() 결과를 표로 담아
    reportlab 으로 PDF를 생성해 바이트로 반환합니다.
    """
    df = get_emotion_report(login_id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("감정 분석 리포트", styles["Title"]))
    elements.append(Paragraph(f"생성일: {datetime.now().date()}", styles["Normal"]))

    # 테이블 데이터
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
