import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
from collections import Counter

# --- 설정 ---
DATA_PATH = r'C:\workspaces\weakend_시각화\data\sentence_test1_250421.xlsx'
POSITIVE = ['긍정']
NEUTRAL  = ['중립']

# --- 키워드 추출 함수 ---
def extract_keywords(texts, top_n=5):
    words = []
    for t in texts:
        words += t.split()
    stopwords = {'은','는','이','가','고','도','을','를','에','의','합니다','했습니다'}
    words = [w for w in words if w not in stopwords and len(w)>1]
    return Counter(words).most_common(top_n)

# --- 데이터 로드 및 감정 분류 ---
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    if path.lower().endswith(('.xls', '.xlsx')):
        tmp = pd.read_excel(path)
    else:
        tmp = pd.read_csv(path)

    cols     = tmp.columns.tolist()
    date_col = next((c for c in cols if 'date' in c.lower()), None)
    emo_col  = next((c for c in cols if '분류' in c or 'emotion' in c.lower()), None)
    text_col = next((c for c in cols if '문장' in c or 'text' in c.lower()), None)

    if date_col is None or emo_col is None or text_col is None:
        st.error(f"날짜·감정·문장 컬럼을 찾을 수 없습니다: {cols}")
        return pd.DataFrame()

    df = pd.DataFrame({
        'date':    pd.to_datetime(tmp[date_col], errors='coerce'),
        'emotion': tmp[emo_col].astype(str),
        'text':    tmp[text_col].astype(str)
    }).dropna(subset=['date','text']).reset_index(drop=True)

    df['category'] = df['emotion'].apply(
        lambda e: '긍정' if e=='긍정'
                  else ('중립' if e=='중립' else '부정')
    )
    return df

# --- 대시보드: 파스텔 그라데이션 게이지 + 메트릭 ---
# --- 대시보드: 파스텔 그라데이션 게이지 + 메트릭 ---
def render_dashboard(df: pd.DataFrame):
    st.header("🎯 대시보드")

    # 1) 최빈 감정 → score (1~3)
    mood      = df['category'].mode().iloc[0]
    score_map = {'부정':1, '중립':2, '긍정':3}
    val       = score_map[mood]

    # 2) 눈금 이모티콘
    emoji_map = {'부정':'☹️','중립':'😐','긍정':'😊'}
    ticks     = [emoji_map['부정'], emoji_map['중립'], emoji_map['긍정']]

    # 3) 파스텔 그라데이션 스텝 생성 (빨강→초록을 화이트와 섞어 부드럽게)
    import numpy as np
    n_steps = 60
    steps = []
    for i, t in enumerate(np.linspace(0, 1, n_steps)):
        # 원색 R,G
        r = int(255 * (1 - t))
        g = int(255 * t)
        # 화이트(255)와 평균내서 파스텔화, B 채널도 화이트 절반
        pastel_r = int((r + 255) / 2)
        pastel_g = int((g + 255) / 2)
        pastel_b = 128
        color = f"rgba({pastel_r},{pastel_g},{pastel_b},1)"

        start = 1 + (3 - 1) * i     / n_steps
        end   = 1 + (3 - 1) * (i+1) / n_steps
        steps.append({'range':[start, end], 'color': color})

    # 4) 게이지 차트
    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=val,
        gauge={
            'axis': {
                'range': [1,3],
                'tickmode': 'array',
                'tickvals': [1,2,3],
                'ticktext': ticks,
                'tickfont': {'size':30}
            },
            'bar': {'color':'black','thickness':0.2},
            'steps': steps,
            'threshold': {
                'line': {'color':'black','width':4},
                'thickness':0.8,
                'value': val
            }
        }
    ))

    # 5) 레이블과 메트릭
    fig.update_layout(
        title="전체 데이터 기반 감정 게이지",
        height=500,
        margin={'t':50,'b':20,'l':0,'r':0},
        annotations=[dict(
            x=1.5, y=-0.15, xref='x', yref='paper',
            text="감정 게이지", showarrow=False,
            font={'size':20,'color':'#666'}
        )]
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6) 긍정/중립/부정 비율 메트릭
    counts = df['category'].value_counts(normalize=True).mul(100).round(1)
    c1, c2, c3 = st.columns(3)
    c1.metric("😊 긍정", f"{counts.get('긍정',0)}%")
    c2.metric("😐 중립", f"{counts.get('중립',0)}%")
    c3.metric("☹️ 부정", f"{counts.get('부정',0)}%")


# --- 감정 트렌드 ---
def render_trend(df: pd.DataFrame):
    st.header("📊 감정 트렌드 분석")
    dates = df['date'].dt.date
    min_d, max_d = dates.min(), dates.max()
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input('시작일', min_value=min_d, max_value=max_d, value=min_d)
    with c2:
        end = st.date_input('종료일', min_value=min_d, max_value=max_d, value=max_d)
    if start > end:
        st.error('시작일이 종료일보다 클 수 없습니다.'); return

    df_f = df[(df['date'].dt.date >= start)&(df['date'].dt.date <= end)].copy()
    if df_f.empty:
        st.warning('선택한 기간에 데이터가 없습니다.'); return

    freq = st.radio('단위', ['일별','주별','월별'], horizontal=True)

    if freq == '일별':
        today    = df_f['date'].dt.date.max()
        df_today = df_f[df_f['date'].dt.date==today]
        counts   = df_today['emotion'].value_counts(normalize=True).mul(100).round(1)
        if counts.empty:
            st.info("오늘의 감정 데이터가 없습니다."); return

        pie_df = counts.reset_index()
        pie_df.columns = ['emotion','percent']
        fig = px.pie(pie_df, names='emotion', values='percent',
                     hole=0.5, title=f"{today} 감정 누적 분포")
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # 오늘의 주요 키워드
        texts = df_today['text'].tolist()
        top_kw = extract_keywords(texts, top_n=5)
        st.subheader("📌 오늘의 주요 키워드")
        for kw, cnt in top_kw:
            st.write(f"- **{kw}** ({cnt}회)")

        return

    if freq == '주별':
        df_f['period'] = df_f['date'] - pd.to_timedelta(df_f['date'].dt.weekday, unit='d')
        title = '주별 감정 비율 흐름'
    else:
        df_f['period'] = df_f['date'].dt.to_period('M').dt.to_timestamp()
        title = '월별 감정 비율 흐름'

    agg   = df_f.groupby(['period','emotion']).size().reset_index(name='count')
    pivot = agg.pivot(index='period', columns='emotion', values='count').fillna(0)
    ratio = pivot.div(pivot.sum(axis=1), axis=0)
    long_df = ratio.reset_index().melt(id_vars='period', var_name='emotion', value_name='ratio')

    fig = px.line(long_df, x='period', y='ratio', color='emotion', markers=True,
                  labels={'period':'기간','ratio':'비율'}, title=title)
    fig.update_layout(legend_title='감정')
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

# --- 감정 달력 ---
def render_calendar(df: pd.DataFrame):
    st.header("📅 감정 달력")
    years = sorted(df['date'].dt.year.unique())
    year  = st.selectbox('연도 선택', years, index=len(years)-1)
    month = st.selectbox('월 선택', list(range(1,13)), index=df['date'].dt.month.max()-1)
    df_m  = df[(df['date'].dt.year==year)&(df['date'].dt.month==month)]
    dom   = df_m.groupby(df_m['date'].dt.day)['category']\
                .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else '')
    emap = {'긍정':'😊','중립':'😐','부정':'☹️'}
    cal  = calendar.Calendar(firstweekday=6).monthdayscalendar(year,month)
    cal_df = pd.DataFrame(cal, columns=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])
    for i, wk in enumerate(cal):
        for j, d in enumerate(wk):
            cal_df.iat[i,j] = f"{d} {emap.get(dom.get(d,''),'')}" if d else ''
    cal_df = cal_df.loc[:, (cal_df!='').any(axis=0)]
    st.table(cal_df)

# --- 알림 탭 ---
def render_alert(df: pd.DataFrame):
    st.header("🔔 맞춤형 알림")
    daily = df.groupby(df['date'].dt.date)['category']\
              .apply(lambda s:(s=='부정').mean())\
              .reset_index(name='neg_ratio')
    if daily.empty:
        st.info('알림 데이터가 없습니다.'); return

    recent = daily['neg_ratio'].iloc[-1]
    flags  = (daily['neg_ratio'] >= 0.5).astype(int)
    consec = flags[::-1].cumprod().sum()

    if recent >= 0.7:
        level, msgs = '[경고]', ['😟 오늘은 정말 많이 힘들었구나','혼자 있지 말고 이야기해보세요']
        show_rec = False
    elif recent >= 0.5 and consec < 3:
        level, msgs = '[주의]', ['🙂 오늘 좀 힘들었지?','조금 휴식해도 괜찮아!']
        show_rec = True
    elif consec >= 3:
        level, msgs = '[주의 지속]', ['☁️ 요 며칠 감정이 무거웠죠?','잠시 쉬어가도 괜찮아요.']
        show_rec = False
    else:
        st.success('현재 특별한 경고가 없습니다. 🙂'); return

    st.markdown(f"**{level} 알림**")
    for m in msgs:
        st.write(f"- {m}")
    if show_rec:
        st.subheader('✨ 추천 콘텐츠')
        st.write("- 오늘은 잠시 눈을 감고 깊게 숨을 쉬어볼까요?")
        st.write("- 좋아하는 음악 한 곡을 들어보세요.")

# --- 메인 함수 ---
def main():
    st.set_page_config(page_title='WEAKEND 감정 리포트', layout='wide')
    df   = load_data(DATA_PATH)
    tabs = st.tabs(['대시보드','감정 트렌드','감정 달력','알림'])
    with tabs[0]:
        render_dashboard(df)
    with tabs[1]:
        render_trend(df)
    with tabs[2]:
        render_calendar(df)
    with tabs[3]:
        render_alert(df)

if __name__ == '__main__':
    main()
