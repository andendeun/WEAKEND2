# app.py
import streamlit as st
import pandas as pd
import altair as alt

# 0) 페이지 설정
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# 1) 모바일 프레임 CSS (360×640px 중앙 박스)
mobile_frame_css = '''
<style>
/* 중앙 모바일 박스 컨테이너 */
[data-testid="stAppViewContainer"] > div:first-child {
    width: 360px !important;
    max-width: 360px !important;
    height: 640px !important;
    margin: 0 auto !important;
    border: 1px solid #ddd !important;
    border-radius: 20px !important;
    overflow: hidden !important;
}
/* 배경 색상 */
[data-testid="stAppViewContainer"] > div:first-child,
[data-testid="stAppViewContainer"] {
    background-color: #faf8f2 !important;
}
</style>
'''
st.markdown(mobile_frame_css, unsafe_allow_html=True)

# 2) 헤더: 로고, Today I feel, 설정 아이콘
col1, col2, col3 = st.columns([1,4,1])
with col1:
    st.image("logo.png", width=80)
with col2:
    st.markdown("## Today I feel", unsafe_allow_html=True)
with col3:
    st.button("⚙️")

# 3) 감정 슬라이더 & 중앙 라벨
emotions = ["SAD", "CALM", "HAPPY"]
current = st.select_slider("", options=emotions, value="CALM", format_func=lambda x: "")
st.markdown(f"<h1 style='text-align:center; margin:0'>{current}</h1>", unsafe_allow_html=True)

# 4) 주간 스냅샷: 요일 + 컬러 도트
dates = pd.date_range(end=pd.Timestamp.today(), periods=7)
df_week = pd.DataFrame({
    "date": dates,
    "emotion": ["SAD","CALM","HAPPY","CALM","SAD","CALM","HAPPY"]
})
cols = st.columns(7)
color_map = {"SAD":"#AADAFF","CALM":"#AAF2BD","HAPPY":"#FFD8A8"}
for d, col in zip(df_week.itertuples(), cols):
    with col:
        st.write(d.date.strftime("%a\n%d"))
        st.markdown(
            f"<div style='width:16px;height:16px;border-radius:50%;background:{color_map[d.emotion]};margin:auto'></div>",
            unsafe_allow_html=True
        )

# 5) 트렌드 라인 차트
df_week["score"] = [1,2,1.5,3,2.5,2,3]
chart = alt.Chart(df_week).mark_line(point=True).encode(
    x=alt.X('date:T', axis=alt.Axis(title=None, labels=False)),
    y=alt.Y('score:Q', axis=alt.Axis(title=None))
).properties(height=150)
st.altair_chart(chart, use_container_width=True)

# 6) 하단 네비게이션 바
st.markdown("---")
nav_cols = st.columns(4)
icons = ["＋","💬","👤","📊"]
for icon, col in zip(icons, nav_cols):
    with col:
        st.button(icon, key=icon)
