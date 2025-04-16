import os
import sqlite3
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


# DB에 대화 내용 저장
def save_message(login_id, role, message, emotion=""):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversations (user_id, role, message, emotion, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (login_id, role, message, emotion, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# 지역 정보 등록
def get_region_list():
    try:
        response = supabase.table("region").select("region_id, region_name").execute()
        region_data = response.data or []
        return [(r["region_name"], r["region_id"]) for r in region_data]  # [(이름, id)] 튜플 리스트
    except Exception as e:
        st.error(f"지역 정보를 불러오지 못했습니다: {e}")
        return []

