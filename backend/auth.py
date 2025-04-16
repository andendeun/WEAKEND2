from backend.db import supabase
from datetime import date

def register(login_id, password, birthdate, regionid, phonenumber, gender):
    try:
        result = supabase.table("users").select("username").eq("username", login_id).execute()
        if len(result.data) > 0:
            return False  # 이미 존재

         # today = date.today().isoformat()

        supabase.table("users").insert({
            "username": login_id,
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

def login(login_id, password):
    result = supabase.table("users").select("password").eq("login_id", login_id).execute()
    if len(result.data) == 0:
        return False
    if result.data[0]["password"] == password:
        # 로그인 성공 시 last_activity 업데이트
        today = str(date.today())
        supabase.table("users").update({"last_activity": today}).eq("login_id", id).execute()
        return True
    return False