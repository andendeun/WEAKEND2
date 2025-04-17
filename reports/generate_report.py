import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
from dotenv import load_dotenv

# Google Fonts에서 불러온 Noto Sans KR 사용
plt.rc('font', family='Noto Sans KR')
plt.rc('axes', unicode_minus=False)

def plot_emotion_trend(login_id: str) -> plt.Figure:
    """
    사용자의 감정 분석 결과를 날짜별로 집계하여 시계열 차트를 반환합니다.
    """
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1) userid 조회
    user_res = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single() \
        .execute()
    if not user_res.data:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "사용자를 찾을 수 없습니다", ha="center", va="center")
        return fig
    user_id = user_res.data["userid"]

    # 2) chat_log에서 chat_id 리스트 가져오기
    logs_res = supabase.table("chat_log") \
        .select("chat_id") \
        .eq("userid", user_id) \
        .execute()
    chat_ids = [r["chat_id"] for r in logs_res.data or []]
    if not chat_ids:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center")
        return fig

    # 3) emotions 테이블에서 해당 chat_id들 가져오기
    em_res = supabase.table("emotions") \
        .select("analysis_date, middle_category_id") \
        .in_("chat_id", chat_ids) \
        .order("analysis_date", desc=False) \
        .execute()
    rows = em_res.data or []
    if not rows:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "감정 분석 데이터가 없습니다", ha="center", va="center")
        return fig

    df = pd.DataFrame(rows)
    df["analysis_date"] = pd.to_datetime(df["analysis_date"]).dt.date

    # 4) 중분류 이름 매핑
    cat_res = supabase.table("middle_categories") \
        .select("middle_category_id, middle_categoryname") \
        .execute()
    cat_df = pd.DataFrame(cat_res.data or [])

    df = df.merge(cat_df, on="middle_category_id", how="left")

    # 5) 그룹화 및 피벗
    pivot = df.groupby(["analysis_date", "middle_categoryname"]) \
              .size() \
              .unstack(fill_value=0)

    # 6) 차트 그리기
    fig, ax = plt.subplots()
    pivot.plot(ax=ax)
    ax.set_title("감정별 발화 빈도 변화")
    ax.set_xlabel("분석 날짜")
    ax.set_ylabel("발화 수")
    ax.legend(title="감정", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    return fig
