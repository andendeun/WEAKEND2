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
        # 필요하다면 emotion_id 같은 정수형 FK도 추가
    }

    try:
        # 반환은 0개~1개를 허용합니다.
        res = supabase.table('emotions_log') \
            .insert(payload) \
            .select('*') \
            .maybe_single() \
            .execute()

        if res.error:
            st.error(f"Insert 실패: {res.error.message}")
            return None

        return res.data

    except APIError as e:
        # e.args[0]에 서버가 보낸 전체 JSON이 담겨 있습니다.
        st.error("APIError 발생! 서버 응답 내용:")
        st.json(e.args[0])
        # 필요하다면 로그에도 남기고, 여기서 리턴하거나 다시 raise 하세요.
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
