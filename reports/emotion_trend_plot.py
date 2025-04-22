import streamlit as st
import pandas as pd
import numpy as np
import calendar
from collections import Counter

# ───────────────────────────────────────────────────────────────────────────────
# 사용자 DB 연동: get_emotion_report 호출
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
    df = get_emotion_report(login_id)
    if df.empty:
        return pd.DataFrame()

    df = df.rename(columns={
        'analysis_date': 'date',
        '분석 날짜': 'date',
        'middle_categoryname': 'emotion',
        '감정 카테고리': 'emotion',
        'chat_content': 'text'
    })
    df['date'] = pd.to_datetime(df['date'])
    if 'text' not in df.columns:
        df['text'] = ''
    df['category'] = df['emotion'].apply(
        lambda e: '긍정' if e == '긍정' else ('중립' if e == '중립' else '부정')
    )
    return df

# --- 대시보드: 파스텔 그라데이션 게이지 + 메트릭 ---
def render_dashboard(df: pd.DataFrame):
    st.header("🎯 대시보드")
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return

    # 점수 매핑
    mood      = df['category'].mode().iloc[0]
    score_map = {'부정':1, '중립':2, '긍정':3}
    val       = score_map[mood]

    # 게이지 스텝 생성
    n_steps = 60
    steps = []
    for i, t in enumerate(np.linspace(0, 1, n_steps)):
        r = int(255 * (1 - t)); g = int(255 * t)
        pastel_r = int((r + 255) / 2); pastel_g = int((g + 255) / 2); pastel_b = 128
        color = f"rgba({pastel_r},{pastel_g},{pastel_b},1)"
        start = 1 + (3 - 1) * i / n_steps
        end   = 1 + (3 - 1) * (i+1) / n_steps
        steps.append({'range':[start, end], 'color': color})

    emoji_map = {'부정':'☹️','중립':'😐','긍정':'😊'}
    ticks     = [emoji_map['부정'], emoji_map['중립'], emoji_map['긍정']]

    try:
        import plotly.graph_objects as go
        import plotly.express as px
        fig = go.Figure(go.Indicator(
            mode="gauge",
            value=val,
            gauge={
                'axis': {'range': [1,3], 'tickmode':'array','tickvals':[1,2,3],'ticktext':ticks,'tickfont':{'size':30}},
                'bar': {'color':'black','thickness':0.2},
                'steps': steps,
                'threshold': {'line':{'color':'black','width':4},'thickness':0.8,'value':val}
            }
        ))
        fig.update_layout(title="전체 대화 기반 감정 게이지", height=450, margin={'t':50,'b':20})
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("Plotly 미설치로 인한 대시보드 그래프 표시 불가")

    counts = df['category'].value_counts(normalize=True).mul(100).round(1)
    c1, c2, c3 = st.columns(3)
    c1.metric("😊 긍정", f"{counts.get('긍정',0)}%")
    c2.metric("😐 중립", f"{counts.get('중립',0)}%")
    c3.metric("☹️ 부정", f"{counts.get('부정',0)}%")

# --- 감정 트렌드 ---
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
    try:
        import plotly.express as px
        if freq == '일별':
            latest = df_f['date'].dt.date.max()
            counts = df_f[df_f['date'].dt.date==latest]['emotion'].value_counts(normalize=True).mul(100).round(1)
            pie_df = counts.reset_index(); pie_df.columns = ['감정','percent']
            fig = px.pie(pie_df, names='감정', values='percent', hole=0.5, title=f"{latest} 감정 분포")
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            if df_f['text'].str.strip().any():
                top_kw = extract_keywords(df_f[df_f['date'].dt.date==latest]['text'].tolist(), top_n=5)
                st.subheader("📌 주요 키워드")
                for kw,cnt in top_kw:
                    st.write(f"- **{kw}** ({cnt}회)")
            return

        # 주별/월별
        if freq == '주별':
            df_f['period'] = df_f['date'] - pd.to_timedelta(df_f['date'].dt.weekday, unit='d')
            title = '주별 감정 비율 흐름'
        else:
            df_f['period'] = df_f['date'].dt.to_period('M').dt.to_timestamp()
            title = '월별 감정 비율 흐름'

        agg = df_f.groupby(['period','emotion']).size().reset_index(name='count')
        pivot = agg.pivot(index='period', columns='emotion', values='count').fillna(0)
        ratio = pivot.div(pivot.sum(axis=1), axis=0)
        long_df = ratio.reset_index().melt(id_vars='period', var_name='감정', value_name='ratio')

        fig = px.line(long_df, x='period', y='ratio', color='감정', markers=True, title=title)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("Plotly 미설치로 인한 트렌드 그래프 표시 불가")

# --- 감정 달력 ---
def render_calendar(df: pd.DataFrame):
    st.header("📅 감정 달력")
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return
    years = sorted(df['date'].dt.year.unique())
    year  = st.selectbox('연도 선택', years, index=len(years)-1)
    month = st.selectbox('월 선택', list(range(1,13)), index=df['date'].dt.month.max()-1)
    df_m = df[(df['date'].dt.year==year)&(df['date'].dt.month==month)]
    dom  = df_m.groupby(df_m['date'].dt.day)['category']\
              .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else '')
    emap = {'긍정':'😊','중립':'😐','부정':'☹️'}
    cal = calendar.Calendar(firstweekday=6).monthdayscalendar(year,month)
    cal_df = pd.DataFrame(cal, columns=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])
    for i, wk in enumerate(cal):
        for j, d in enumerate(wk):
            cal_df.iat[i,j] = f"{d} {emap.get(dom.get(d,''),'')}" if d else ''
    cal_df = cal_df.loc[:, (cal_df!='').any(axis=0)]
    st.table(cal_df)

# --- 알림 탭 ---
def render_alert(df: pd.DataFrame):
    st.header("🔔 맞춤형 알림")
    if df.empty:
        st.info("알림 데이터가 없습니다.")
        return
    daily = df.groupby(df['date'].dt.date)['category']\
              .apply(lambda s: (s=='부정').mean())\
              .reset_index(name='neg_ratio')
    recent = daily['neg_ratio'].iloc[-1]
    flags  = (daily['neg_ratio'] >= 0.5).astype(int)
    consec = flags[::-1].cumprod().sum()

    if recent >= 0.7:
        level, msgs = '[경고]', ['😟 오늘 많이 힘들었네요','혼자 있지 말고 이야기해요']
        show_rec = False
    elif recent >= 0.5 and consec < 3:
        level, msgs = '[주의]', ['🙂 오늘 좀 힘들었죠?','휴식을 권해요']
        show_rec = True
    elif consec >= 3:
        level, msgs = '[주의 지속]', ['☁️ 최근 며칠 감정이 무거웠어요','잠시 쉬어도 괜찮아요']
        show_rec = False
    else:
        st.success('특별한 경고가 없습니다. 🙂')
        return

    st.markdown(f"**{level} 알림**")
    for m in msgs:
        st.write(f"- {m}")
    if show_rec:
        st.subheader('✨ 추천 콘텐츠')
        st.write('- 오늘 좋아하는 음악을 들어보세요.')
        st.write('- 잠시 눈을 감고 심호흡을 해보세요.')
