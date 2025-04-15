import streamlit as st
import speech_recognition as sr
import re

from auth import register, login
from chatbot import generate_response
from db import save_message

from inference import predict, predict_emotion_from_text
from log_emotions import log_emotion
from gpt_feedback import get_gpt_feedback
from analyze_flow import generate_emotion_plot
from generate_pdf import generate_pdf

# --- 앱 초기 설정 ---
st.set_page_config(page_title="☀️WEAKEND☀️", layout="centered")
st.markdown("""
    <style>
        .block-container {
            max-width: 450px;
            min-height: 2000px;
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
    </style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "auth_page" not in st.session_state:
    st.session_state.auth_page = None

# --- 로그인 상태일 때 ---
if st.session_state["logged_in"]:
    st.title("☀️WEAKEND☀️")
    st.sidebar.markdown(f"👤 **{st.session_state['username']}** 님, 안녕하세요! 😊")

    st.sidebar.title("Menu")
    selected = st.sidebar.radio("List", ["내 감정 입력하기", "감정 리포트"])

    if selected == "내 감정 입력하기":
        username = st.session_state["username"]
        audio_file = st.file_uploader("🗣 오늘 하루는 어땠나요?", type=["wav", "mp3"])
        user_text = ""

        if audio_file:
            st.audio(audio_file)
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data, language="ko-KR")
                st.success("음성 인식 성공")
            except:
                st.error("음성 인식 실패")

        user_input = st.text_area("또는 텍스트로 입력하기", value=user_text)

        if st.button("감정 분석 시작") and user_input.strip():
            # 1. 감정 예측
            emotion = predict_emotion_from_text(user_input)
            st.write(f"예측된 감정: **{emotion}**")

            # 2. 로그 저장
            log_emotion(username, emotion, user_input)
            save_message(username, "user", user_input)

            # 3. GPT 피드백 생성
            gpt_reply = get_gpt_feedback(user_input, emotion)
            save_message(username, "assistant", gpt_reply)
            st.markdown(f"**GPT 상담사:** {gpt_reply}")

            # 4. 감정 흐름 시각화
            st.image(generate_emotion_plot(username))

            # 5. PDF 리포트 다운로드
            pdf_path = make_pdf_report(username)
            with open(pdf_path, "rb") as f:
                st.download_button("📄 감정 리포트 PDF 다운로드", f, file_name="emotion_report.pdf")

    elif selected == "감정 리포트":
        st.subheader("My Emotion Report")
        st.write("🛠 준비 중입니다...")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.rerun()

# --- 로그인/회원가입 페이지 ---
else:
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>☀️ WEAKEND ☀️</h1>", unsafe_allow_html=True)
    st.image("mainimage.png", use_container_width=True)

    if st.button("🔐 로그인", use_container_width=True):
        st.session_state.auth_page = "로그인"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.button("📝 회원가입", use_container_width=True):
        st.session_state.auth_page = "회원가입"

    if st.session_state.auth_page == "로그인":
        st.subheader("로그인")
        user = st.text_input("아이디")
        passwd = st.text_input("비밀번호", type="password")
        if st.button("로그인 확인"):
            if login(user, passwd):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success("로그인 성공! 🎉")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    elif st.session_state.auth_page == "회원가입":
        st.subheader("회원가입")
        new_user = st.text_input("아이디")
        new_pass = st.text_input("비밀번호", type="password")
        if st.button("회원가입 확인"):
            if register(new_user, new_pass):
                st.success("회원가입 완료! 로그인 해주세요.")
                st.session_state.auth_page = "로그인"
            else:
                st.error("이미 가입된 아이디입니다.")