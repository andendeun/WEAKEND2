import os
import tempfile

from backend.chatbot import generate_response
from backend.db import save_message
from inference import predict_emotion_from_text
from log_emotion import log_emotion
from reports.generate_report import generate_html_report
from reports.emotion_trend_plot import plot_emotion_trend
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")

# 💬 말풍선 UI 스타일 추가
st.markdown("""
    <style>
    .user-bubble {
        background-color: #DCF8C6;
        padding: 10px 15px;
        border-radius: 12px;
        max-width: 75%;
        margin: 5px;
        text-align: right;
        align-self: flex-end;
    }
    .bot-bubble {
        background-color: #F1F0F0;
        padding: 10px 15px;
        border-radius: 12px;
        max-width: 75%;
        margin: 5px;
        text-align: left;
        align-self: flex-start;
    }
    .emotion-bubble {
        background-color: #FFF8E1;
        padding: 5px 10px;
        border-radius: 8px;
        font-size: 0.9em;
        color: #555;
        max-width: 60%;
        margin: 2px auto;
        text-align: center;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 🔀 사이드바 탭 선택
page = st.sidebar.radio("탭 선택", ["내 감정 입력하기", "감정 리포트", "리포트 다운로드"])

# ──────────────────────────────
# 1️⃣ 감정 입력 탭
# ──────────────────────────────
if page == "내 감정 입력하기":
    st.title("☀️WEAKEND 감정 상담 챗봇")

    username = st.text_input("🙋‍♀️ 이름을 입력해주세요", value="사용자")

    audio_file = st.file_uploader("🎤 음성 파일을 업로드하세요 (WAV)", type=["wav"])
    user_input = ""

    if audio_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_file.read())
            user_input = transcribe_audio(tmp_file.name)
        st.success(f"📝 변환된 텍스트: {user_input}")
    else:
        user_input = st.text_input("✏️ 감정을 표현해보세요")

    if user_input:
        # 1. GPT 챗봇 응답
        bot_reply = generate_response(user_input)

        # 2. 감정 분석 (사용자 입력만)
        emotion, confidence = predict_emotion_from_text(user_input)

        # 3. 저장
        save_message("user", user_input)
        save_message("bot", bot_reply)
        log_emotion(username, emotion, confidence)

        # 4. 대화 기록 저장
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", bot_reply))
        st.session_state.chat_history.append(("emotion", f"{emotion} ({confidence*100:.2f}%)"))

    # 💬 대화 말풍선 출력
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
# 2️⃣ 감정 리포트 탭
# ──────────────────────────────
elif page == "감정 리포트":
    st.title("📈 감정 변화 리포트")
    username = st.text_input("이름을 입력하세요", value="사용자")
    fig = generate_emotion_plot(username)
    st.pyplot(fig)

# ──────────────────────────────
# 3️⃣ 리포트 다운로드 탭
# ──────────────────────────────
elif page == "리포트 다운로드":
    st.title("📄 감정 리포트 PDF 다운로드")
    username = st.text_input("이름을 입력하세요", value="사용자")
    if st.button("📥 PDF 저장하기"):
        pdf_path = generate_pdf(username)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📩 리포트 다운로드",
                data=f,
                file_name=f"{username}_감정리포트.pdf",
                mime="application/pdf"
            )
