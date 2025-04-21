import os
import tempfile
import speech_recognition as sr
import re
from datetime import date
from backend.auth import register, login
from backend.chatbot import generate_response
from reports import plot_emotion_trend, get_emotion_report, create_pdf_report
import pandas as pd
import matplotlib.pyplot as plt
from backend.db import get_region_list
from backend.log_emotions import log_emotion

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 0) 페이지 설정 & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")

st.markdown("""
    <style>
        .block-container {
            max-width: 450px;
            height: 640px;         /* 세로 고정 */
            overflow-y: auto;      /* 내부 스크롤 */
            margin: 40px auto;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 30px 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
        }
        body {
            background-color: #f1f3f6;
        }
        h1 { font-size: 28px !important; text-align: center; }
        h3 { font-size: 18px !important; text-align: center; }
        button { font-size: 16px !important; }
        .chat-container { max-height: 300px; overflow-y: auto; }
        .chat-bubble { display: flex; gap: 10px; align-items: flex-start; }
        .user-bubble-wrapper { display: flex; justify-content: flex-end; }
        .user-bubble {
            background-color: #A8E6CF; padding: 12px 16px;
            border-radius: 18px 18px 0 18px; max-width:75%;
            word-break: break-word;
        }
        .bot-bubble {
            background-color: #ECECEC; padding: 12px 16px;
            border-radius: 18px 18px 18px 0; max-width:75%;
            word-break: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1) 세션 상태 초기화
# ─────────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "login"       # login, signup, main
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ─────────────────────────────────────────────────────────────────────────────
# 2) 페이지별 함수 정의
# ─────────────────────────────────────────────────────────────────────────────
def login_page():
    st.markdown("<h1>☀️ WEAKEND ☀️</h1>", unsafe_allow_html=True)
    st.image("mainimage.png", use_container_width=True)
    st.subheader("🔐 로그인")

    user = st.text_input("아이디")
    passwd = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if login(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success("로그인 성공! 🎉")
        else:
            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    st.markdown("---")
    if st.button("📝 회원가입"):
        st.session_state.page = "signup"


def signup_page():
    st.markdown("<h1>📝 회원가입</h1>", unsafe_allow_html=True)
    st.image("mainimage.png", use_container_width=True)

    login_id = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    birthdate = st.date_input(
        "생년월일",
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )

    region_options = get_region_list()
    region_name_to_id = dict(region_options)
    region_name = st.selectbox("거주지역", list(region_name_to_id.keys()))
    region_id = region_name_to_id.get(region_name)

    phonenumber = st.text_input("핸드폰번호 (예: 010-1234-5678)")
    gender = st.selectbox("성별", ["남성", "여성"])

    if st.button("회원가입하기"):
        if not re.match(r"^010
