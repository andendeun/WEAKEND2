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
from reports.emotion_trend_plot import load_data, render_dashboard, render_trend, render_calendar, render_alert
from streamlit_option_menu import option_menu
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 0) 페이지 설정 & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")
st.markdown("""
    <style>
        .block-container { max-width: 414px; height: 896px; overflow-y: auto;
            margin: 40px auto; background-color: white; border: 1px solid #ddd;
            border-radius: 20px; padding: 30px 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
        body { background-color: #f1f3f6; }
        h1 { font-size:28px!important;text-align:center; }
        h3 { font-size:18px!important;text-align:center; }
        button { font-size:16px!important; }
        .chat-container { max-height:300px; overflow-y:auto; }
        .chat-bubble { display:flex; gap:10px; align-items:flex-start; }
        .user-bubble-wrapper { display:flex; justify-content:flex-end; }
        .user-bubble { background-color:#218AFF; color:#FFF;
            padding:12px 16px; border-radius:18px 18px 0 18px;
            max-width:75%; word-break:break-word; }
        .bot-bubble { background-color:#f2f2f2;
            padding:12px 16px; border-radius:18px 18px 18px 0;
            max-width:75%; word-break:break-word; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1) 세션 상태 초기화
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("page", "login"),
    ("logged_in", False),
    ("username", ""),
    ("chat_history", []),
    ("chat_input", ""),
    ("active_page", "내 감정 알아보기"),  # ← 이 줄을 추가
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# 2) 페이지별 함수 정의
# ─────────────────────────────────────────────────────────────────────────────
def login_page():
    st.image("mainimage.png", use_container_width=True)
    user = st.text_input("아이디")
    passwd = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if login(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.page = "main"
            st.success("로그인 성공! 메인 페이지로 이동합니다.")
        else:
            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
    st.markdown("---")
    if st.button("회원가입"):
        st.session_state.page = "signup"


def signup_page():
    st.markdown("<h1>회원가입</h1>", unsafe_allow_html=True)
    login_id = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    birthdate = st.date_input("생년월일", min_value=date(1900,1,1), max_value=date.today())
    region_options = get_region_list()
    region_name_to_id = dict(region_options)
    region = st.selectbox("거주지역", list(region_name_to_id.keys()))
    ph = st.text_input("핸드폰번호 (010-1234-5678)")
    gender = st.selectbox("성별", ["남성","여성"])
    if st.button("회원가입하기"):
        if not re.match(r"^010-\d{4}-\d{4}$", ph):
            st.error("전화번호 형식이 올바르지 않습니다.")
        else:
            ok,msg = register(login_id, password,
                              birthdate.strftime("%Y-%m-%d"),
                              region_name_to_id[region], ph, gender)
            if ok:
                st.success("회원가입 완료!")
                st.session_state.page = "login"
            else:
                st.error(msg)
    st.markdown("---")
    if st.button("← 로그인으로 돌아가기"):
        st.session_state.page = "login"


def main_page():
    if st.session_state.active_page not in ["내 감정 알아보기","감정 리포트"]:
        st.session_state.active_page = "내 감정 알아보기"
    page = option_menu(None, ["내 감정 알아보기","감정 리포트"],
                       icons=["pencil-square","heart"],
                       default_index=["내 감정 알아보기","감정 리포트"].index(st.session_state.active_page),
                       orientation="horizontal")

    if page == "내 감정 알아보기":
        st.title("당신의 감정을 입력해 보세요")
        audio_file = st.file_uploader("🎤 RECORD", type=["wav","mp3"])
        text = ""
        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_file.read())
                rec = sr.Recognizer()
                with sr.AudioFile(tmp.name) as src:
                    data = rec.record(src)
                    try:
                        text = rec.recognize_google(data, language="ko-KR")
                        st.success(f"📝 변환된 텍스트: {text}")
                    except:
                        st.warning("음성 인식 실패. 텍스트로 입력해주세요.")
        # 메시지 전송 콜백 정의
        def send_message():
            msg = st.session_state.chat_input.strip()
            if msg:
                log_emotion(st.session_state.username, 'user', msg)
                reply = generate_response(msg)
                log_emotion(st.session_state.username, 'bot', reply)
                st.session_state.chat_history.append(('user', msg))
                st.session_state.chat_history.append(('bot', reply))
            st.session_state.chat_input = ""
        # 입력창 및 전송 버튼
        st.text_input("📝 CHAT", value=text, key="chat_input", on_change=lambda: None)
        st.button("전송", key="send_button", on_click=send_message)

        # 대화 표시
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for u, b in zip(st.session_state.chat_history[::2], st.session_state.chat_history[1::2]):
            st.markdown(f"""
                <div class="user-bubble-wrapper">
                  <div class="user-bubble">{u[1]}</div>
                </div>
                <div class="chat-bubble">
                  <img src="https://cdn-icons-png.flaticon.com/512/8229/8229494.png" width="24" />
                  <div class="bot-bubble">{b[1]}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.title("감정 리포트")
        df = load_data(st.session_state.username)
        if df.empty:
            st.warning("로그인 후 대화를 먼저 진행해 주세요."); return
        tabs = st.tabs(["대시보드","감정 트렌드","감정 달력","맞춤 알림"])
        render_dashboard(df) if tabs[0] else None
        render_trend(df) if tabs[1] else None
        render_calendar(df) if tabs[2] else None
        render_alert(df) if tabs[3] else None
        pdf = create_pdf_report(st.session_state.username)
        st.download_button("📥 PDF", data=pdf,
                           file_name=f"{st.session_state.username}_감정리포트_{date.today()}.pdf",
                           mime="application/pdf")

    # 로그아웃
    col1, _ = st.columns([3,1])
    with col1:
        if st.button("로그아웃"):
            st.session_state.logged_in=False
            st.session_state.page="login"
            st.session_state.chat_history=[]

# ─────────────────────────────────────────────────────────────────────────────
# 3) 라우팅
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
else:
    main_page()
