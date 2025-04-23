from datetime import date, datetime
from inference import predict_emotion_with_score
from backend.db import supabase, get_userid_by_login

def log_emotion(login_id: str, role: str, message: str) -> None:
    # 0) 로그인된 user_id 조회
    user_id = get_userid_by_login(login_id)
    if user_id is None:
        raise ValueError(f"Unknown login_id: {login_id}")

    # 1) chat_log에는 user/bot 구분 없이 모두 저장
    try:
        chat_ins = supabase.table("chat_log").insert({
            "userid":       user_id,
            "chat_time":    datetime.now().isoformat(),
            "chat_content": message,
            "chat_role":    role
            }).execute()
    except Exception as e:
        print(f"[Warning] chat_log insert failed: {e}")
        return
    
     # chat_ins에서 생성된 chat_id를 꺼내 옵니다
    chat_id = chat_ins.data[0]["chat_id"]


    # 2) 오직 role="user" 일 때만 emotions 테이블에 분석 결과 저장
    if role == "user":
        label, score = predict_emotion_with_score(message)
        cat = supabase.table("middle_categories")\
            .select("middle_category_id","main_category_id")\
            .eq("middle_categoryname", label)\
            .single()\
            .execute().data
        try:
            supabase.table("emotions").insert({
                "chat_id":            chat_id,
                "main_category_id":   cat["main_category_id"],
                "middle_category_id": cat["middle_category_id"],
                "emotion_score":      score,
                "analysis_date":      date.today().isoformat()
            }).execute()
        except Exception as e:
            print(f"[Warning] emotions insert failed: {e}")
