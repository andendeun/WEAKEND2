# 10_streamlit_ui.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os
from datetime import datetime

# 📁 파일 경로 설정
FEEDBACK_PATH = "D:/workspace/Project/logs/gpt_feedback_log_cleaned.csv"
FONT_PATH = "D:/workspace/Project/fonts/NotoSansKR-Regular.ttf"

# ✅ 폰트 설정 (한글 깨짐 방지)
font_name = fm.FontProperties(fname=FONT_PATH).get_name()
plt.rcParams['font.family'] = font_name

# ✅ 데이터 로드 함수
@st.cache_data
def load_data():
    df = pd.read_csv(FEEDBACK_PATH, quotechar='"')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    return df

# ✅ 감정 분포 시각화
def plot_emotion_distribution(df):
    st.subheader("📊 감정 대분류 분포")
    if '보완_대분류' in df.columns:
        counts = df['보완_대분류'].value_counts()
        fig, ax = plt.subplots()
        counts.plot(kind='bar', ax=ax)
        ax.set_xlabel("감정 대분류")
        ax.set_ylabel("빈도")
        ax.set_title("감정 분포")
        st.pyplot(fig)
    else:
        st.warning("감정 대분류 컬럼이 없습니다.")

# ✅ Streamlit 앱 실행
st.set_page_config(page_title="감정 피드백 리포트", layout="wide")
st.title("🧠 감정 피드백 기록 뷰어")

df = load_data()

# ✅ 사이드바 필터
st.sidebar.header("🔍 검색 및 필터")
search_text = st.sidebar.text_input("문장 내용 검색")
start_date = st.sidebar.date_input("시작일", df['timestamp'].min().date())
end_date = st.sidebar.date_input("종료일", df['timestamp'].max().date())

# ✅ 필터 적용
filtered_df = df.copy()
if search_text:
    filtered_df = filtered_df[filtered_df['input_text'].str.contains(search_text, case=False, na=False)]

filtered_df = filtered_df[(filtered_df['timestamp'] >= pd.to_datetime(start_date)) &
                          (filtered_df['timestamp'] <= pd.to_datetime(end_date))]

# ✅ 시각화
plot_emotion_distribution(filtered_df)

# ✅ 피드백 테이블 출력
st.subheader("📄 감정 피드백 목록")
for i, row in filtered_df.iterrows():
    st.markdown(f"**🕒 {row['timestamp']} | ✏️ 입력 문장:** `{row['input_text']}`")
    st.markdown("**💌 감정 피드백:**")
    st.markdown(row.get("user_feedback", row.get("gpt_feedback", "(피드백 없음)")))
    st.divider()