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
        if not re.match(r"^010-\d{4}-\d{4}$", phonenumber):
            st.error("전화번호 형식이 올바르지 않습니다.")
        else:
            success, msg = register(
                login_id=login_id,
                password=password,
                birthdate=birthdate.strftime("%Y-%m-%d"),
                region_id=region_id,
                phonenumber=phonenumber,
                gender=gender
            )
            if success:
                st.success("회원가입 완료! 로그인 페이지로 이동합니다.")
                st.session_state.page = "login"
            else:
                st.error(msg)

    st.markdown("---")
    if st.button("← 로그인으로 돌아가기"):
        st.session_state.page = "login"


def main_page():
    # ─── 사이드바 탭
    if "active_page" not in st.session_state:
        st.session_state.active_page = "내 감정 입력하기"

    page = st.sidebar.radio(
        "탭 선택",
        ["내 감정 입력하기", "감정 리포트", "맞춤형 컨텐츠 추천"],
        index=["내 감정 입력하기","감정 리포트","맞춤형 컨텐츠 추천"]
              .index(st.session_state.active_page)
    )

    # 1️⃣ 내 감정 입력하기
    if page == "내 감정 입력하기":
        st.title("☀️WEAKEND 감정 상담 챗봇")
        audio_file = st.file_uploader("🎤 음성 파일 업로드 (wav/mp3)", type=["wav","mp3"])
        user_input = ""

        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_file.read())
                recognizer = sr.Recognizer()
                with sr.AudioFile(tmp.name) as src:
                    audio_data = recognizer.record(src)
                    try:
                        user_input = recognizer.recognize_google(audio_data, language="ko-KR")
                        st.success(f"📝 변환된 텍스트: {user_input}")
                    except:
                        st.warning("음성 인식 실패. 텍스트로 입력해주세요.")

        if not user_input:
            user_input = st.text_input("✏️ 감정을 표현해 보세요")

        if user_input:
            log_emotion(st.session_state.username, "user", user_input)
            bot_reply = generate_response(user_input)
            log_emotion(st.session_state.username, "bot", bot_reply)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", bot_reply))

        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        paired = list(zip(st.session_state.chat_history[::2],
                          st.session_state.chat_history[1::2]))
        for u_msg, b_msg in reversed(paired):
            st.markdown(f'''
                <div class="user-bubble-wrapper">
                  <div class="user-bubble">{u_msg[1]}</div>
                </div>
                <div class="chat-bubble">
                  <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" width="24" />
                  <div class="bot-bubble">{b_msg[1]}</div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2️⃣ 감정 리포트
    elif page == "감정 리포트":
        st.title("📊 감정 변화 트렌드")
        report_df = get_emotion_report(st.session_state.username)
        report_df["분석 날짜"] = pd.to_datetime(report_df["분석 날짜"]).dt.date
        min_date, max_date = report_df["분석 날짜"].min(), report_df["분석 날짜"].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", value=min_date,
                                       min_value=min_date, max_value=max_date, key="start_date")
        with col2:
            end_date = st.date_input("종료일", value=max_date,
                                     min_value=min_date, max_value=max_date, key="end_date")

        period = st.radio("집계 단위", ["일별","주별","월별"], horizontal=True)
        fig = plot_emotion_trend(st.session_state.username, start_date, end_date, period)
        if fig:
            st.pyplot(fig)
        else:
            st.warning("선택한 기간에 데이터가 없습니다.")

        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            pdf_bytes = create_pdf_report(st.session_state.username)
            st.download_button("📥 PDF 다운로드", data=pdf_bytes,
                               file_name=f"{st.session_state.username}_감정리포트_{date.today()}.pdf",
                               mime="application/pdf")

    # 3️⃣ 맞춤형 컨텐츠 추천
    else:
        st.title("🎯 맞춤형 컨텐츠 추천")
        st.write("서비스 준비 중입니다...")

    # 로그아웃
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.session_state.chat_history = []

# ─────────────────────────────────────────────────────────────────────────────
# 3) 라우팅: 로그인 상태/페이지 분기
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.page == "signup":
        signup_page()
    else:
        login_page()
else:
    main_page()
