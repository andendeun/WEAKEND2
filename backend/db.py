import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv


load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def get_userid_by_login(login_id: str) -> int | None:
    """login_id로부터 users.userid를 조회해서 반환"""
    res = supabase.table("users") \
        .select("userid") \
        .eq("login_id", login_id) \
        .single() \
        .execute()
    return res.data["userid"] if res.data else None

def save_message(login_id: str, role: str, message: str, emotion: str = "") -> None:
    """
    Supabase의 chat_log 테이블에 저장합니다.
    - userid: users.userid (int)
    - chat_time: 현재 시각
    - chat_content: message (text)
    - chat_role: role (varchar)
    """
    user_id = get_userid_by_login(login_id)
    if user_id is None:
        raise ValueError(f"Unknown login_id: {login_id}")

    supabase.table("chat_log").insert({
        "userid":        user_id,
        "chat_time":     datetime.now().isoformat(),
        "chat_content":  message,
        "chat_role":     role
    }).execute()
