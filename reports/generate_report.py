import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

def get_emotion_report(login_id: str) -> pd.DataFrame:
    """
    사용자별 감정 분석 결과를 DataFrame 으로 반환합니다.
    """
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # userid 조회
    u = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single() \
        .execute()
    user_id = u.data["userid"]

    # chat_log + emotions JOIN
    resp = supabase.table("emotions") \
        .select("analysis_date, emotion_score, middle_category_id") \
        .eq("chat_log.userid", user_id, foreign_table="chat_log") \
        .order("analysis_date", desc=False) \
        .execute()
    rows = resp.data or []
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 카테고리 이름 매핑
    cat = supabase.table("middle_categories") \
        .select("middle_category_id, middle_categoryname") \
        .execute()
    cat_df = pd.DataFrame(cat.data or [])
    df = df.merge(cat_df, on="middle_category_id", how="left")

    # 컬럼 순서 정리
    df = df[["analysis_date", "middle_categoryname", "emotion_score"]]
    df.columns = ["분석 날짜", "감정 카테고리", "감정 확신도"]
    return df
