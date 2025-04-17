import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

def get_emotion_report(login_id: str) -> pd.DataFrame:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1) userid 조회
    user = supabase.table("users")\
        .select("userid")\
        .eq("login_id", login_id)\
        .single().execute()
    if not user.data:
        return pd.DataFrame()
    user_id = user.data["userid"]

    # 2) 사용자의 chat_id 리스트 가져오기
    logs = supabase.table("chat_log")\
        .select("chat_id")\
        .eq("userid", user_id)\
        .execute().data or []
    chat_ids = [r["chat_id"] for r in logs]
    if not chat_ids:
        return pd.DataFrame()

    # 3) emotions 테이블에서 해당 chat_id들 가져오기
    resp = supabase.table("emotions")\
        .select("analysis_date, emotion_score, middle_category_id")\
        .in_("chat_id", chat_ids)\
        .order("analysis_date", desc=False)\
        .execute()
    rows = resp.data or []
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 4) 카테고리 이름 합치기
    cat = supabase.table("middle_categories")\
        .select("middle_category_id, middle_categoryname")\
        .execute().data or []
    cat_df = pd.DataFrame(cat)
    df = df.merge(cat_df, on="middle_category_id", how="left")

    # 5) 컬럼 정리
    df = df[["analysis_date", "middle_categoryname", "emotion_score"]]
    df.columns = ["분석 날짜", "감정 카테고리", "감정 확신도"]
    return df
