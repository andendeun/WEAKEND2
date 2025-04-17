import os
from datetime import date, datetime
from supabase import create_client
from dotenv import load_dotenv
from inference import predict_emotion_with_score
from backend.db import supabase, get_userid_by_login

def log_emotion(login_id: str, role: str, message: str) -> None:
    # 1) userid 조회
    user = supabase.table("users")\
        .select("userid")\
        .eq("login_id", login_id)\
        .single()\
        .execute()
    user_id = user.data["userid"]

    # 2) chat_log INSERT
    chat_ins = supabase.table("chat_log").insert({
        "userid":       user_id,
        "chat_time":    datetime.now().isoformat(),
        "chat_content": message,
        "chat_role":    role,
        "emotion":      None
    }).execute()
    chat_id = chat_ins.data[0]["chat_id"]

    # 3) 감정 예측+확신도 추출
    label, score = predict_emotion_with_score(message)

    # 4) 중·대분류 아이디 조회
    cat = supabase.table("middle_categories")\
        .select("middle_category_id", "main_category_id")\
        .eq("middle_categoryname", label)\
        .single()\
        .execute()
    mid_id  = cat.data["middle_category_id"]
    main_id = cat.data["main_category_id"]

    # 5) emotions 테이블에 INSERT
    supabase.table("emotions").insert({
        "chat_id":            chat_id,
        "main_category_id":   main_id,
        "middle_category_id": mid_id,
        "emotion_score":      score,  
        "analysis_date":      date.today().isoformat()
    }).execute()
