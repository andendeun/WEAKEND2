import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def register(user_id, password):
    # 유저 중복 확인 (id 기준)
    result = supabase.table("users").select("id").eq("id", user_id).execute()
    if len(result.data) > 0:
        return False  # 이미 존재하는 사용자

    today = date.today().isoformat()

    # 최소 필수 정보만 입력
    supabase.table("users").insert({
        "id": user_id,
        "password": password,
        "signup_date": today,
        "role": "user"  # 기본 역할
    }).execute()

    return True

def login(user_id, password):
    result = supabase.table("users").select("password").eq("id", user_id).execute()
    if len(result.data) == 0:
        return False
    return result.data[0]["password"] == password
