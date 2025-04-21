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

# ▶ 페이지 설정
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")
st.markdown("""
    <style>
        .block-container {
            max-width: 414px;
            min-height: 896px;
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
            
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-top: 20px;
            max-height: 500px;
            overflow-y: auto;
        }

        .chat-bubble {
            display: flex;
            gap: 10px;
            align-items: flex-start;
        }

        .chat-bubble img {
            width: 32px;
            height: 32px;
            border-radius: 50%;
        }

        .user-bubble-wrapper {
            display: flex;
            justify-content: flex-end;
        }

        .user-bubble {
            background-color: #A8E6CF;
            padding: 12px 16px;
            border-radius: 18px 18px 0px 18px;
            max-width: 75%;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .bot-bubble {
            background-color: #ECECEC;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 0px;
            max-width: 75%;
            white-space: pre-wrap;
            word-break: break-word;
        }
    </style> 
""", unsafe_allow_html=True)

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
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    elif st.session_state.get("auth_page") == "회원가입":
        st.subheader("회원가입")
        login_id = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        birthdate = st.date_input(
            "생년월일",
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )

        region_options = get_region_list()
        region_name_to_id = dict(region_options)  # { "서울": 1, "경기": 2, ... }
        region_name = st.selectbox("거주지역", list(region_name_to_id.keys()))
        region_id = region_name_to_id.get(region_name)

        phonenumber = st.text_input("핸드폰번호")

        if phonenumber and not re.match(r"^010-\d{4}-\d{4}$", phonenumber):
            st.error("핸드폰번호 형식이 올바르지 않습니다. 예: 010-0000-0000")
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
                    st.success(msg)
                    st.session_state["auth_page"] = "로그인"
                else:
                    st.error(msg)


# ─────────────────────────────────────────────────────────────────────────────
# 2) 메인 (챗봇/리포트) 페이지 함수
#    (기존 3개 탭: 내 감정 입력하기, 감정 리포트, 리포트 다운로드)
# ─────────────────────────────────────────────────────────────────────────────
def show_main_page():
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "내 감정 입력하기"
    page = st.sidebar.radio(
        "탭 선택",
        ["내 감정 입력하기", "감정 리포트", "맞춤형 컨텐츠 추천"],
        index=["내 감정 입력하기", "감정 리포트", "맞춤형 컨텐츠 추천"].index(st.session_state["active_page"])
    )
    username = st.session_state["username"]

    # ──────────────────────────────
    # 1️⃣ 감정 입력 탭 (기존 코드 유지)
    # ──────────────────────────────
    if page == "내 감정 입력하기":
        st.title("☀️WEAKEND 감정 상담 챗봇")

        audio_file = st.file_uploader("🎤 음성 파일을 업로드하세요 (WAV)", type=["wav","mp3"])
        user_input = ""

        if audio_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.read())
                recognizer = sr.Recognizer()
                with sr.AudioFile(tmp_file.name) as source:
                    audio_data = recognizer.record(source)
                    try:
                        user_input = recognizer.recognize_google(audio_data, language="ko-KR")
                        st.success(f"📝 변환된 텍스트: {user_input}")
                    except:
                        st.warning("음성 인식 실패. 텍스트로 입력해주세요.")

        if not user_input:
            user_input = st.text_input("✏️ 감정을 표현해보세요")

        if user_input:
            # 1) 유저 메시지 저장 및 감정 분석
            log_emotion(st.session_state["username"], "user", user_input)
            # 2) 챗봇 응답 (DB 기록 없음)
            bot_reply = generate_response(user_input)
            # 3) 챗봇 답변 저장 및 감정 분석
            log_emotion(st.session_state["username"], "bot", bot_reply)
            # 4) 세션에 대화 내역 쌓기 (화면 표시용)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot",  bot_reply))

        # 쌍 단위 최신순 말풍선 출력
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        paired_history = list(zip(st.session_state.chat_history[::2], st.session_state.chat_history[1::2]))
        paired_history.reverse()

        for user_msg, bot_msg in paired_history:
            user_text = user_msg[1]
            bot_text = bot_msg[1]

            st.markdown(f'''
                <div class="user-bubble-wrapper">
                    <div class="user-bubble">{user_text}</div>
                </div>
                <div class="chat-bubble" style="gap: 10px; margin-bottom: 24px;">
                    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" width="24" height="24" style="margin-top: 4px;" />
                    <div class="bot-bubble">{bot_text}</div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


    # ──────────────────────────────
    # 2️⃣ 감정 리포트 탭 (기존 코드 유지)
        # ──────────────────────────────
    elif page == "감정 리포트":
        st.title("📊 감정 변화 트렌드")

        # — 1) 조회 기간
        # report_df = get_emotion_report(username)
        # report_df["분석 날짜"] = pd.to_datetime(report_df["분석 날짜"]).dt.date
        # min_date = report_df["분석 날짜"].min()
        # max_date = report_df["분석 날짜"].max()

        # start_date, end_date = st.date_input(
        #     "조회 기간",                 # 첫 번째 인자는 레이블
        #     [min_date, max_date],       # 리스트 형태로 범위 지정
        #     min_value=min_date,
        #     max_value=max_date,
        #     key="date_range"             # key만 붙여주세요
        # )


        report_df = get_emotion_report(username)
        report_df["분석 날짜"] = pd.to_datetime(report_df["분석 날짜"]).dt.date
        min_date = report_df["분석 날짜"].min()
        max_date = report_df["분석 날짜"].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                label="시작일",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                label="종료일",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="end_date"
            )

        # — 2) 집계 단위
        period = st.radio(
            "집계 단위",
            ["일별", "주별", "월별"],
            index=0,
            horizontal=True
        )

        # — 3) 차트 그리기
        fig = plot_emotion_trend(username, start_date, end_date, period)
        if fig:
            st.pyplot(fig)
        else:
            st.warning("선택한 기간에는 감정 데이터가 없습니다.")

        # — 4) PDF 다운로드 버튼 가운데 정렬
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pdf_bytes = create_pdf_report(username)
            st.download_button(
                label="📥 리포트 PDF 다운로드",
                data=pdf_bytes,
                file_name=f"{username}_감정리포트_{date.today()}.pdf",
                mime="application/pdf"
            )

    # ──────────────────────────────
    # 3️⃣ 맞춤형 컨텐츠 추천
    # ──────────────────────────────
    elif page == "맞춤형 컨텐츠 추천":
        st.title("맞춤형 컨텐츠 추천")











    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["chat_history"] = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 3) 최종 실행 로직
# ─────────────────────────────────────────────────────────────────────────────

# # TEST용 로그인 모드
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False

# if not st.session_state["logged_in"]:
#     st.session_state["username"] = "test002"
#     st.session_state["password"] = "test002"
#     st.session_state["logged_in"] = True
#     st.session_state["active_page"] = "감정 리포트"   # 메인으로 볼 거 설정

# st.write("로그인된 사용자:", st.session_state.get("username"))
# show_main_page()


# 배포 시
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    show_login_page()
else:
    show_main_page()
