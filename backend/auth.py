from backend.db import supabase
from datetime import datetime


def register(login_id, password, birthdate, region_id, phonenumber, gender):
    try:
        # 1. 중복 ID 확인
        id_check = supabase.table("users").select("login_id").eq("login_id", login_id).execute()
        print("🟡 ID 중복 조회 결과:", id_check.data)

        if id_check.data and len(id_check.data) > 0:
            return False, "이미 존재하는 아이디입니다."

        # 2. 중복 전화번호 확인
        phone_check = supabase.table("users").select("phonenumber").eq("phonenumber", phonenumber).execute()
        print("🟡 전화번호 중복 조회 결과:", phone_check.data)

        if phone_check.data and len(phone_check.data) > 0:
            return False, "이미 가입된 전화번호입니다."

        # 3. 회원 정보 삽입
        insert_result = supabase.table("users").insert({
            "login_id": login_id,
            "password": password,
            "birthdate": birthdate,
            "region_id": region_id,
            "phonenumber": phonenumber,
            "gender": gender,
            "last_activity": datetime.now().isoformat()
        }).execute()

        print("✅ Insert 결과:", insert_result.data)

        return True, "회원가입 성공"

    except Exception as e:
        print("❌ 회원가입 오류:", e)
        return False, "서버 오류가 발생했습니다."
    
    
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