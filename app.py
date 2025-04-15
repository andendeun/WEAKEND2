import os
import tempfile

import speech_recognition as sr
import re

# ▶ 추가: 로그인/회원가입 함수를 import해 사용
from backend.auth import register, login

# ▶ 기존 코드 유지
from backend.chatbot import generate_response
from backend.db import init_db
from inference import predict_emotion_from_text
from log_emotion import log_emotion
from reports.generate_report import generate_html_report
from reports.emotion_trend_plot import plot_emotion_trend

import streamlit as st

# ▶ 페이지 설정
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")

# ▶ 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ─────────────────────────────────────────────────────────────────────────────
# 1) 로그인/회원가입 페이지 함수
# ─────────────────────────────────────────────────────────────────────────────
def show_login_page():
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>☀️ WEAKEND ☀️</h1>", unsafe_allow_html=True)
    st.image("mainimage.png", use_container_width=True)

    # 로그인/회원가입 이동 버튼
    if st.button("🔐 로그인", use_container_width=True):
        st.session_state.auth_page = "로그인"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.button("📝 회원가입", use_container_width=True):
        st.session_state.auth_page = "회원가입"

    # 실제 로그인/회원가입 폼
    if st.session_state.get("auth_page") == "로그인":
        st.subheader("로그인")
        user = st.text_input("아이디")
        passwd = st.text_input("비밀번호", type="password")
        if st.button("로그인 확인"):
            if login(user, passwd):
                st.session_state["logged_in"] = True
                st.session_state["username"] = user
                st.success("로그인 성공! 🎉")
                st.experimental_rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    elif st.session_state.get("auth_page") == "회원가입":
        st.subheader("회원가입")
        new_user = st.text_input("아이디")
        new_pass = st.text_input("비밀번호", type="password")
        if st.button("회원가입 확인"):
            if register(new_user, new_pass):
                st.success("회원가입 완료! 로그인 해주세요.")
                st.session_state["auth_page"] = "로그인"
            else:
                st.error("이미 가입된 아이디입니다.")

# ─────────────────────────────────────────────────────────────────────────────
# 2) 메인 (챗봇/리포트) 페이지 함수
#    (기존 3개 탭: 내 감정 입력하기, 감정 리포트, 리포트 다운로드)
# ─────────────────────────────────────────────────────────────────────────────
def show_main_page():
    # 사이드바 탭 선택
    page = st.sidebar.radio("탭 선택", ["내 감정 입력하기", "감정 리포트", "리포트 다운로드"])

    # ──────────────────────────────
    # 1️⃣ 감정 입력 탭 (기존 코드 유지)
    # ──────────────────────────────
    if page == "내 감정 입력하기":
        st.title("☀️WEAKEND 감정 상담 챗봇")

        username = st.text_input("🙋‍♀️ 이름을 입력해주세요", value=st.session_state["username"])

        audio_file = st.file_uploader("🎤 음성 파일을 업로드하세요 (WAV)", type=["wav"])
        user_input = ""

        # ▼ 음성 인식 부분
        if audio_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.read())
                # transcribe_audio 함수가 있다면 여기서 호출
                # user_input = transcribe_audio(tmp_file.name)
            st.success(f"📝 변환된 텍스트: {user_input}")
        else:
            user_input = st.text_input("✏️ 감정을 표현해보세요")

        if user_input:
            # 1. GPT 챗봇 응답
            bot_reply = generate_response(user_input)

            # 2. 감정 분석 (사용자 입력만)
            emotion, confidence = predict_emotion_from_text(user_input)

            # 3. 저장 - (※ init_db() 가 DB 초기화 함수인지, save_message() 대체인지 확인 필요)
            init_db("user", user_input)  # <-- 원본 코드 그대로
            init_db("bot", bot_reply)
            log_emotion(username, emotion, confidence)

            # 4. 대화 기록
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", bot_reply))
            st.session_state.chat_history.append(("emotion", f"{emotion} ({confidence*100:.2f}%)"))

        # 말풍선 출력
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for sender, msg in st.session_state.chat_history:
            if sender == "user":
                st.markdown(f'<div class="user-bubble">{msg}</div>', unsafe_allow_html=True)
            elif sender == "bot":
                st.markdown(f'<div class="bot-bubble">{msg}</div>', unsafe_allow_html=True)
            elif sender == "emotion":
                st.markdown(f'<div class="emotion-bubble">🧠 감정 분석: {msg}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────
    # 2️⃣ 감정 리포트 탭 (기존 코드 유지)
    # ──────────────────────────────
    elif page == "감정 리포트":
        st.title("📈 감정 변화 리포트")
        username = st.text_input("이름을 입력하세요", value=st.session_state["username"])
        fig = plot_emotion_trend(username)
        st.pyplot(fig)

    # ──────────────────────────────
    # 3️⃣ 리포트 다운로드 탭 (기존 코드 유지)
    # ──────────────────────────────
    elif page == "리포트 다운로드":
        st.title("📄 감정 리포트 PDF 다운로드")
        username = st.text_input("이름을 입력하세요", value=st.session_state["username"])
        if st.button("📥 PDF 저장하기"):
            pdf_path = generate_html_report(username)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📩 리포트 다운로드",
                    data=f,
                    file_name=f"{username}_감정리포트.pdf",
                    mime="application/pdf"
                )

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["chat_history"] = []
        st.experimental_rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 3) 최종 실행 로직
#    (로그인 여부 확인해서 페이지 보여주기)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    # 로그인 안 된 상태 => 로그인 페이지
    show_login_page()
else:
    # 로그인 성공 상태 => 메인 페이지
    show_main_page()
