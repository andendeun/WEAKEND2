import os
import tempfile
import speech_recognition as sr
import re
from datetime import date
from backend.auth import register, login
from backend.chatbot import generate_response
from reports import create_pdf_report
import pandas as pd
import matplotlib.pyplot as plt
from backend.db import get_region_list
from backend.log_emotions import log_emotion
from reports.emotion_trend_plot import (
    load_data, render_dashboard, render_trend, render_calendar, render_alert
)
from streamlit_option_menu import option_menu
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 0) 페이지 설정 & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")
st.markdown("""
  <style>
    .block-container { max-width:414px; height:896px; overflow-y:auto; margin:40px auto;
                      background-color:white; border:1px solid #ddd; border-radius:20px;
                      padding:30px 20px; box-shadow:0 8px 24px rgba(0,0,0,0.05); }
    body { background-color:#f1f3f6; }
    h1 { font-size:28px!important; text-align:center; }
    h3 { font-size:18px!important; text-align:center; }
    .chat-container { max-height:300px; overflow-y:auto; }
    .chat-bubble { display:flex; gap:10px; align-items:flex-start; }
    .user-bubble-wrapper { display:flex; justify-content:flex-end; }
    .user-bubble { background-color:#218AFF; color:#FFF; padding:12px 16px;
                    border-radius:18px 18px 0 18px; max-width:75%; word-break:break-word; }
    .bot-bubble { background-color:#f2f2f2; padding:12px 16px;
                  border-radius:18px 18px 18px 0; max-width:75%; word-break:break-word; }
  </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1) 세션 상태 초기화
# ─────────────────────────────────────────────────────────────────────────────
for key in ("page","logged_in","username","chat_history"):
    if key not in st.session_state:
        default = [] if key=="chat_history" else False if key=="logged_in" else ""
        st.session_state[key] = default
st.session_state.page = st.session_state.page or "login"

# ─────────────────────────────────────────────────────────────────────────────
# 2) 페이지별 함수 정의
# ─────────────────────────────────────────────────────────────────────────────
def login_page():
    st.image("mainimage.png", use_container_width=True)
    user = st.text_input("아이디", key="login_user")
    pwd  = st.text_input("비밀번호", type="password", key="login_pwd")
    if st.button("로그인", key="login_btn"):
        if login(user, pwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.page = "main"
            st.success("로그인 성공! 메인 페이지로 이동합니다.")
        else:
            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
    st.markdown("---")
    if st.button("회원가입", key="to_signup"):
        st.session_state.page = "signup"

def signup_page():
    st.markdown("<h1>회원가입</h1>", unsafe_allow_html=True)
    login_id  = st.text_input("아이디", key="su_user")
    password  = st.text_input("비밀번호", type="password", key="su_pwd")
    birthdate = st.date_input("생년월일", min_value=date(1900,1,1),
                              max_value=date.today(), key="su_birth")
    region_options   = get_region_list()
    region_name     = st.selectbox("거주지역", [r[0] for r in region_options], key="su_region")
    region_id       = dict(region_options).get(region_name)
    phonenumber     = st.text_input("핸드폰번호 (010-1234-5678)", key="su_phone")
    gender          = st.selectbox("성별", ["남성","여성"], key="su_gender")
    if st.button("회원가입하기", key="signup_btn"):
        if not re.match(r"^010-\d{4}-\d{4}$", phonenumber):
            st.error("전화번호 형식이 올바르지 않습니다.")
        else:
            success, msg = register(
                login_id=login_id, password=password,
                birthdate=birthdate.strftime("%Y-%m-%d"),
                region_id=region_id, phonenumber=phonenumber, gender=gender
            )
            if success:
                st.success("회원가입 완료! 로그인 페이지로 돌아갑니다.")
                st.session_state.page = "login"
            else:
                st.error(msg)
    st.markdown("---")
    if st.button("← 로그인으로 돌아가기", key="back_login"):
        st.session_state.page = "login"

def main_page():
    # 네비메뉴
    page = option_menu(
        menu_title=None,
        options=["내 감정 알아보기","감정 리포트"],
        icons=["pencil-square","heart"],
        default_index=0 if st.session_state.page=="main" else 1,
        orientation="horizontal", key="
