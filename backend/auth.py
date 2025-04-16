import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def register(user_id, password, birthdate, regionid, phonenumber, gender):
    # 유저 중복 확인 (id 기준)
    result = supabase.table("users").select("id").eq("id", user_id).execute()
    if len(result.data) > 0:
        return False  # 이미 존재하는 사용자

    today = date.today().isoformat()

    # 최소 필수 정보만 입력
    supabase.table("users").insert({
        "id": id,
        "password": password,
        "birthyear": birthdate,
        "region": regionid,
        "phonenumber": phonenumber,
        "gender": gender,
        "signup_date": today,
        "role": "user"
    }).execute()

    return True

def login(user_id, password):
    result = supabase.table("users").select("password").eq("id", user_id).execute()
    if len(result.data) == 0:
        return False
    if result.data[0]["password"] == password:
        # 로그인 성공 시 last_activity 업데이트
        today = str(date.today())
        supabase.table("users").update({"last_activity": today}).eq("id", id).execute()
        return True
    return False