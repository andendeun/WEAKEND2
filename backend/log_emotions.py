from datetime import date, datetime
from inference import predict_emotion_with_score
from backend.db import supabase, get_userid_by_login

import streamlit as st
from postgrest import APIError

def log_emotion(username, role, user_input):
    payload = {
        'username': username,
        'role':     role,
        'message':  user_input,
    }

    try:
        # ← 여기부터 바꿔주세요
        res = supabase.table('emotions_log') \
            .insert(payload) \
            .execute()
        # ← 여기까지 (방법 1)
        
        if res.error:
            st.error(f"Insert 실패: {res.error.message}")
            return None
        return res.data
    except APIError as e:
        st.error(f"APIError: {e.args[0]}")
        return None


    # 2) 오직 role="user" 일 때만 emotions 테이블에 분석 결과 저장
    if role == "user":
        label, score = predict_emotion_with_score(message)
        cat = supabase.table("middle_categories")\
            .select("middle_category_id","main_category_id")\
            .eq("middle_categoryname", label)\
            .single()\
            .execute().data
        supabase.table("emotions").insert({
            "chat_id":            chat_id,
            "main_category_id":   cat["main_category_id"],
            "middle_category_id": cat["middle_category_id"],
            "emotion_score":      score,
            "analysis_date":      date.today().isoformat()
        }).execute()
