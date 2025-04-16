import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def register(user_id, password, birthdate, regionid, phonenumber, gender):
    try:
        result = supabase.table("users").select("username").eq("username", id).execute()
        if len(result.data) > 0:
            return False  # 이미 존재

         # today = date.today().isoformat()

        supabase.table("users").insert({
            "username": id,
            "password": password,
            "birthdate": birthdate,
            "region": regionid,
            "phonenumber": phonenumber,
            "gender": gender,
            "last_activity": date.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        print("❌ 회원가입 실패:", e)
        return False

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