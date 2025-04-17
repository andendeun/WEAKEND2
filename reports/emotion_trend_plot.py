import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
from dotenv import load_dotenv

def plot_emotion_trend(login_id: str) -> plt.Figure:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1) userid 조회
    u = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single() \
        .execute()
    user_id = u.data["userid"]

    # 2) emotions 테이블에서 필요한 컬럼 가져오기
    resp = supabase.table("emotions") \
        .select("analysis_date, middle_category_id") \
        .eq("chat_log.userid", user_id, foreign_table="chat_log") \
        .order("analysis_date", desc=False) \
        .execute()
    rows = resp.data or []
    if not rows:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center")
        return fig

    df = pd.DataFrame(rows)
    df["analysis_date"] = pd.to_datetime(df["analysis_date"]).dt.date

    # 3) 카테고리 이름 매핑
    cat = supabase.table("middle_categories") \
        .select("middle_category_id, middle_categoryname") \
        .execute()
    cat_df = pd.DataFrame(cat.data or [])
    df = df.merge(cat_df, on="middle_category_id", how="left")

    # 4) 날짜별, 감정별 발화 수 집계
    pivot = df.groupby(["analysis_date", "middle_categoryname"]) \
              .size() \
              .unstack(fill_value=0)

    # 5) 차트 그리기
    fig, ax = plt.subplots()
    pivot.plot(ax=ax)
    ax.set_title("감정별 발화 빈도 변화")
    ax.set_xlabel("분석 날짜")
    ax.set_ylabel("발화 수")
    ax.legend(title="감정", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    return fig
