import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def get_userid_by_login(login_id: str) -> int | None:
    """login_id로 users.userid를 조회"""
    res = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single() \
        .execute()
    return (res.data or {}).get("userid")


# DB에 대화 내용 저장
def save_message(login_id: str, role: str, message: str) -> None:
    """Supabase chat_log 테이블에 대화 기록을 남깁니다."""
    user_id = get_userid_by_login(login_id)
    if user_id is None:
        raise ValueError(f"Unknown login_id: {login_id}")
    supabase.table("chat_log").insert({
        "userid":       user_id,
        "chat_time":    datetime.now().isoformat(),
        "chat_content": message,
        "chat_role":    role
    }).execute()


# 지역 정보 등록
def get_region_list():
    try:
        response = supabase.table("region").select("region_id, region_name").execute()
        region_data = response.data or []
        return [(r["region_name"], r["region_id"]) for r in region_data]  # [(이름, id)] 튜플 리스트
    except Exception as e:
        st.error(f"지역 정보를 불러오지 못했습니다: {e}")
        return []

