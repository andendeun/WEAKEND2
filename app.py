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
        .block-container {
            max-width: 414px;
            height: 896px;         /* 세로 고정 */
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
            background-color: #218AFF;  /* iMessage 블루 톤 */
            color: #FFFFFF;             /* 흰 글씨 */
            padding: 12px 16px;
            border-radius: 18px 18px 0 18px;
            max-width: 75%;
            word-break: break-word;
        }
        .bot-bubble {
            background-color: #f2f2f2;   /* 짙은 회색 톤 */
            padding: 12px 16px;
            border-radius: 18px 18px 18px 0;
            max-width: 75%;
            word-break: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1) 세션 상태 초기화
# ─────────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "login"      # login, signup, main
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
    st.image("mainimage.png", use_container_width=True)
    user = st.text_input("아이디", key="login_user")
    passwd = st.text_input("비밀번호", type="password", key="login_passwd")

    if st.button("로그인", key="login_btn"):
        if login(user, passwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.page = "main"
            st.success("로그인 성공! 메인 페이지로 이동합니다.")
        else:
            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    st.markdown("---")
    if st.button("회원가입", key="go_signup"):
        st.session_state.page = "signup"


def signup_page():
    st.markdown("<h1>회원가입</h1>", unsafe_allow_html=True)
    login_id = st.text_input("아이디", key="signup_user")
    password = st.text_input("비밀번호", type="password", key="signup_passwd")
    birthdate = st.date_input(
        "생년월일", min_value=date(1900, 1, 1), max_value=date.today(), key="signup_birth"
    )

    region_options = get_region_list()
    region_name_to_id = dict(region_options)
    region_name = st.selectbox("거주지역", list(region_name_to_id.keys()), key="signup_region")
    region_id = region_name_to_id.get(region_name)

    phonenumber = st.text_input("핸드폰번호 (예: 010-1234-5678)", key="signup_phone")
    gender = st.selectbox("성별", ["남성", "여성"], key="signup_gender")

    if st.button("회원가입하기", key="signup_btn"):
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
                st.success("회원가입 완료!")
                st.session_state.page = "login"
            else:
                st.error(msg)

    st.markdown("---")
    if st.button("← 로그인으로 돌아가기", key="back_to_login"):
        st.session_state.page = "login"


def main_page():
    if "active_page" not in st.session_state:
        st.session_state.active_page = "내 감정 알아보기"

    page = option_menu(
        menu_title=None,
        options=["내 감정 알아보기", "감정 리포트"],
        icons=["pencil-square", "heart"],
        default_index=["내 감정 알아보기", "감정 리포트"]
                       .index(st.session_state.active_page),
        orientation="horizontal",
        styles={
            "container": {"padding":"0!important", "background-color":"#f1f3f6"},
            "nav-link": {"font-size":"16px", "padding":"0 20px"},
            "nav-link-selected": {"background-color":"#0976bc", "font-weight":"bold"},
        },
        key="main_menu"
    )
    st.session_state.active_page = page

    # ─────────────────────────────────────────────────────────────────────────
    if page == "내 감정 알아보기":
        st.title("당신의 감정을 입력해 보세요")

        # 1) 음성 업로드 & 플래그 초기화
        audio_file = st.file_uploader(
            label="🎤 RECORD ",
            type=["wav", "mp3"],
            key="audio_uploader"
        )
        if "last_audio" not in st.session_state:
            st.session_state.last_audio = None
            st.session_state.audio_processed = False

        cur_audio = audio_file.name if audio_file else None
        if cur_audio != st.session_state.last_audio:
            st.session_state.last_audio = cur_audio
            st.session_state.audio_processed = False

        # 2) 음성 인식
        recognized_text = ""
        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_file.read())
                r = sr.Recognizer()
                with sr.AudioFile(tmp.name) as src:
                    audio_data = r.record(src)
                    try:
                        recognized_text = r.recognize_google(audio_data, language="ko-KR")
                        st.success(f"📝 변환된 텍스트: {recognized_text}")
                    except:
                        st.warning("음성 인식 실패. 텍스트로 입력해주세요.")

        # 3) 음성 텍스트 자동 처리 (한 번만)
        if recognized_text and not st.session_state.audio_processed:
            user_msg = recognized_text
            log_emotion(st.session_state.username, "user", user_msg)
            bot_reply = generate_response(user_msg)
            log_emotion(st.session_state.username, "bot", bot_reply)

            st.session_state.chat_history.append(("user", user_msg))
            st.session_state.chat_history.append(("bot", bot_reply))
            st.session_state.audio_processed = True

        # 4) 수동 채팅 폼
        with st.form("chat_form", clear_on_submit=True):
            chat_text = st.text_input("📝 CHAT", placeholder="메시지를 입력하세요", key="chat_input")
            submitted = st.form_submit_button("전송", use_container_width=True, key="send_btn")

        if submitted and chat_text:
            log_emotion(st.session_state.username, "user", chat_text)
            bot_reply = generate_response(chat_text)
            log_emotion(st.session_state.username, "bot", bot_reply)

            st.session_state.chat_history.append(("user", chat_text))
            st.session_state.chat_history.append(("bot", bot_reply))

        # 5) 대화 내용 렌더링
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        paired = list(zip(st.session_state.chat_history[::2],
                          st.session_state.chat_history[1::2]))
        for u_msg, b_msg in reversed(paired):
            st.markdown(f'''
                <div class="user-bubble-wrapper">
                  <div class="user-bubble">{u_msg[1]}</div>
                </div>
                <div class="chat-bubble">
                  <img src="https://cdn-icons-png.flaticon.com/512/8229/8229494.png" width="24" />
                  <div class="bot-bubble">{b_msg[1]}</div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    elif page == "감정 리포트":
        st.title("감정 리포트")

        df = load_data(st.session_state.username)
        if df.empty:
            st.warning("로그인 후 대화를 먼저 진행해 주세요.")
            return

        tab1, tab2, tab3, tab4 = st.tabs(
            ["대시보드", "감정 트렌드", "감정 달력", "맞춤 알림"],
            key="report_tabs"
        )
        with tab1:
            render_dashboard(df)
        with tab2:
            render_trend(df)
        with tab3:
            render_calendar(df)
        with tab4:
            render_alert(df)

        pdf_bytes = create_pdf_report(st.session_state.username)
        st.download_button(
            "📥 PDF Download",
            data=pdf_bytes,
            file_name=f"{st.session_state.username}_감정리포트_{date.today()}.pdf",
            mime="application/pdf",
            key="download_pdf"
        )

    # 로그아웃
    logout_col, _ = st.columns([3, 1])
    with logout_col:
        if st.button("로그아웃", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.session_state.chat_history = []

# ─────────────────────────────────────────────────────────────────────────────
# 3) 라우팅
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
else:
    main_page()
