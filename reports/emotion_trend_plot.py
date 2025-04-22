import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
from collections import Counter
from reports.generate_report import get_emotion_report

# --- 키워드 추출 함수 ---
def extract_keywords(texts, top_n=5):
    words = []
    for t in texts:
        words += t.split()
    stopwords = {'은','는','이','가','고','도','을','를','에','의','합니다','했습니다'}
    words = [w for w in words if w not in stopwords and len(w)>1]
    return Counter(words).most_common(top_n)

# --- 데이터 로드 및 전처리 ---
@st.cache_data
def load_data(login_id: str) -> pd.DataFrame:
    """
    DB에서 감정 로그를 가져와서 분석용 DataFrame으로 변환합니다.
    Columns: ['date', 'emotion', 'text', 'category']
    """
    df = get_emotion_report(login_id)
    if df.empty:
        return pd.DataFrame()
    # 컬럼명 통일
    df = df.rename(columns={
        'analysis_date': 'date', '분석 날짜': 'date',
        'middle_categoryname': 'emotion', '감정 카테고리': 'emotion',
        'chat_content': 'text'
    })
    df['date'] = pd.to_datetime(df['date'])
    if 'text' not in df.columns:
        df['text'] = ''
    df['category'] = df['emotion'].apply(
        lambda e: '긍정' if e=='긍정' else ('중립' if e=='중립' else '부정')
    )
    return df

# --- 대시보드: Plotly Pie 차트 + 메트릭 ---
def render_dashboard(df: pd.DataFrame):
    st.header("🎯 대시보드")
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return
    latest = df['date'].dt.date.max()
    today_df = df[df['date'].dt.date == latest]
    counts = today_df['category'].value_counts(normalize=True).mul(100).round(1)
    pie_df = counts.reset_index()
    pie_df.columns = ['감정','percent']

    fig = px.pie(
        pie_df,
        names='감정',
        values='percent',
        hole=0.5,
        title=f"{latest} 감정 분포"
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

    # 메트릭 표시
    c1, c2, c3 = st.columns(3)
    c1.metric("😊 긍정", f"{counts.get('긍정',0)}%")
    c2.metric("😐 중립", f"{counts.get('중립',0)}%")
    c3.metric("☹️ 부정", f"{counts.get('부정',0)}%")

# --- 감정 트렌드: Plotly Line 차트 ---
def render_trend(df: pd.DataFrame):
    st.header("📊 감정 트렌드 분석")
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return
    dates = df['date'].dt.date
    min_d, max_d = dates.min(), dates.max()
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input('시작일', min_value=min_d, max_value=max_d, value=min_d)
    with c2:
        end = st.date_input('종료일', min_value=min_d, max_value=max_d, value=max_d)
    if start > end:
        st.error('시작일이 종료일보다 클 수 없습니다.')
        return
    df_f = df[(df['date'].dt.date >= start) & (df['date'].dt.date <= end)].copy()
    if df_f.empty:
        st.warning('선택한 기간에 데이터가 없습니다.')
        return

    freq = st.radio('단위', ['일별','주별','월별'], horizontal=True)
    if freq == '일별':
        # 일별 분포는 대시보드 재사용
        render_dashboard(df_f)
        return

    # 주별/월별 기간 컬럼 생성
    if freq == '주별':
        df_f['period'] = df_f['date'] - pd.to_timedelta(df_f['date'].dt.weekday, unit='d')
    else:
        df_f['period'] = df_f['date'].dt.to_period('M').dt.to_timestamp()

    # 집계 및 비율 계산
    agg = df_f.groupby(['period','category']).size().reset_index(name='count')
    pivot = agg.pivot(index='period', columns='category', values='count').fillna(0)
    ratio = pivot.div(pivot.sum(axis=1), axis=0)
    long_df = (
        ratio
        .reset_index()
        .melt(id_vars='period', var_name='감정', value_name='비율')
    )

    fig = px.line(
        long_df,
        x='period',
        y='비율',
        color='감정',
        markers=True,
        labels={'period':'기간','비율':'비율'},
        title=f"{freq} 감정 비율 흐름"
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

# --- 감정 달력 ---
def render_calendar(df: pd.DataFrame):
    st.header("📅 감정 달력")
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return
    years = sorted(df['date'].dt.year.unique())
    year = st.selectbox('연도 선택', years, index=len(years)-1)
    # 기록된 월만 목록으로
    months = sorted(df[df['date'].dt.year == year]['date'].dt.month.unique())
    month = st.selectbox('월 선택', months, index=len(months)-1)
    df_m = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]
    dom = df_m.groupby(df_m['date'].dt.day)['category']
    dom = dom.apply(lambda s: s.mode().iloc[0] if not s.mode().empty else '')
    emap = {'긍정':'😊','중립':'😐','부정':'☹️'}
    cal = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    cal_df = pd.DataFrame(cal, columns=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])
    for i, week in enumerate(cal):
        for j, d in enumerate(week):
            cal_df.iat[i,j] = f"{d} {emap.get(dom.get(d,''),'')}" if d else ''
    cal_df = cal_df.loc[:, (cal_df!='').any(axis=0)]
    st.table(cal_df)

# --- 맞춤 알림 ---
def render_alert(df: pd.DataFrame):
    st.header("🔔 맞춤형 알림")
    if df.empty:
        st.info("알림 데이터가 없습니다.")
        return
    daily = df.groupby(df['date'].dt.date)['category']
    daily = daily.apply(lambda s: (s=='부정').mean()).reset_index(name='neg_ratio')
    recent = daily['neg_ratio'].iloc[-1]
    flags = (daily['neg_ratio'] >= 0.5).astype(int)
    consec = flags.iloc[::-1].cumprod().sum()

    if recent >= 0.7:
        level, msgs = '[경고]', ['😟 매우 힘든 날이네요','누군가에게 이야기해보세요']
        show_rec = False
    elif recent >= 0.5 and consec < 3:
        level, msgs = '[주의]', ['🙂 오늘 힘들었죠?','조금 쉬어보세요']
        show_rec = True
    elif consec >= 3:
        level, msgs = '[주의 지속]', ['☁️ 최근 감정이 무겁네요','잠시 쉬어가도 좋아요']
        show_rec = False
    else:
        st.success('특별한 경고가 없습니다. 🙂')
        return

    st.markdown(f"**{level} 알림**")
    for m in msgs:
        st.write(f"- {m}")
    if show_rec:
        st.subheader('✨ 추천 콘텐츠')
        st.write('- 좋아하는 음악을 들어보세요.')
        st.write('- 눈을 감고 심호흡 해보세요.')
