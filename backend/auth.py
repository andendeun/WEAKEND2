from backend.db import supabase
from datetime import date

def register(login_id, password, birthdate, region_id, phonenumber, gender):
    try:
        # 안전하게 None 검사
        result = supabase.table("users").select("login_id").eq("login_id", login_id).execute()
        existing_users = result.data if result.data else []

        if len(existing_users) > 0:
            return False  # 이미 존재

        # INSERT
        supabase.table("users").insert({
            "login_id": login_id,
            "password": password,
            "birthdate": birthdate,
            "region_id": region_id,
            "phonenumber": phonenumber,
            "gender": gender,
            "last_activity": date.today().isoformat()
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
        supabase.table("users").update({"last_activity": today}).eq("login_id", login_id).execute()
        return True
    return False