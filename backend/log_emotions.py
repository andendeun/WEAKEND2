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
        res = supabase.table('emotions')\
            .insert(payload)\
            .execute()

        if res.error:
            st.error("Insert 실패:")
            st.error(res.error.message)         # Supabase‑py가 잡아준 에러 메시지
            return None
        return res.data

    except APIError as e:
        # 1) args
        st.error(f"APIError.args: {e.args!r}")
        # 2) 가능하면 response 속성
        if hasattr(e, "response"):
            st.error(f"Status code: {e.response.status_code}")
            st.text("response.text:")
            st.code(e.response.text, language="json")
        else:
            st.error("`e.response` 속성이 없습니다.")
        # 3) 그리고 나서 다시 raise 해 줘야 로그에 기록됩니다.
        raise


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
