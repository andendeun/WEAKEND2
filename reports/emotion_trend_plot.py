import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
from collections import Counter

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
    # 여기서만 동적 import
    from reports.generate_report import get_emotion_report
    df = get_emotion_report(login_id)

    if df.empty:
        return pd.DataFrame()

    df = df.rename(columns={
        'analysis_date': 'date',
        '분석 날짜':     'date',
        'middle_categoryname': 'emotion',
        '감정 카테고리':        'emotion',
        'chat_content':        'text'
    })

    df['date'] = pd.to_datetime(df['date'])
    if 'text' not in df.columns:
        df['text'] = ''
    df['category'] = df['emotion'].apply(
        lambda e: '긍정' if e=='긍정'
                  else ('중립' if e=='중립' else '부정')
    )
    return df


# --- 대시보드: Plotly Pie 차트 + 메트릭 ---
def render_dashboard(df: pd.DataFrame):
    if df.empty:
        st.info("분석할 감정 데이터가 없습니다.")
        return

    mood      = df['category'].mode().iloc[0]
    score_map = {'부정':1, '중립':2, '긍정':3}
    val       = score_map[mood]
    emoji_map = {'부정':'☹️','중립':'😐','긍정':'😊'}
    ticks     = [emoji_map['부정'], emoji_map['중립'], emoji_map['긍정']]

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

    fig.update_layout(
        title="▶ 감정 게이지",
        height=600,
        width=350,
        autosize=False,
        margin={'t':30,'b':10,'l':0,'r':0},
        annotations=[dict(
            x=1.5, y=-0.15, xref='x', yref='paper',
            text="감정 게이지", showarrow=False,
            font={'size':20,'color':'#666'}
        )]
    )
    st.plotly_chart(fig, use_container_width=False)

    counts = df['category'].value_counts(normalize=True).mul(100).round(1)
    c1, c2, c3 = st.columns(3)
    c1.metric("😊 긍정", f"{counts.get('긍정',0)}%")
    c2.metric("😐 중립", f"{counts.get('중립',0)}%")
    c3.metric("☹️ 부정", f"{counts.get('부정',0)}%")




# --- 감정 트렌드: Plotly Line 차트 ---
def render_trend(df: pd.DataFrame):
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

    freq = st.radio('조회기준', ['일별','주별','월별'], horizontal=True)

    if freq == '일별':
        today    = df_f['date'].dt.date.max()
        df_today = df_f[df_f['date'].dt.date==today]
        counts   = df_today['emotion'].value_counts(normalize=True).mul(100).round(1)
        if counts.empty:
            st.info("오늘의 감정 데이터가 없습니다."); return

        pie_df = counts.reset_index()
        pie_df.columns = ['emotion','percent']
        fig = px.pie(pie_df, names='emotion', values='percent',
                     hole=0.5, title=f"▶ 감정 분포")
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=False)

        # 오늘의 주요 키워드
        texts = df_today['text'].tolist()
        top_kw = extract_keywords(texts, top_n=5)
        st.markdown("<h3 style='text-align:left;'>📌 오늘의 주요 키워드</h3>", unsafe_allow_html=True)
        for kw, cnt in top_kw:
            st.write(f"- **{kw}** ({cnt}회)")

        return

    if freq == '주별':
        df_f['period'] = df_f['date'] - pd.to_timedelta(df_f['date'].dt.weekday, unit='d')
        title = '▶ 주차별 감정 흐름'
    else:
        df_f['period'] = df_f['date'].dt.to_period('M').dt.to_timestamp()
        title = '▶ 월별 감정 흐름'

    agg   = df_f.groupby(['period','emotion']).size().reset_index(name='count')
    pivot = agg.pivot(index='period', columns='emotion', values='count').fillna(0)
    ratio = pivot.div(pivot.sum(axis=1), axis=0)
    long_df = ratio.reset_index().melt(id_vars='period', var_name='emotion', value_name='ratio')

    fig = px.line(long_df, x='period', y='ratio', color='emotion', markers=True,
                  labels={'period':'기간','ratio':'비율'}, title=title)
    fig.update_layout(legend_title='감정')
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=False)



# --- 감정 달력 ---
def render_calendar(df: pd.DataFrame):
    years = sorted(df['date'].dt.year.unique())
    year  = st.selectbox('연도 선택', years, index=len(years)-1)
    months = list(range(1, 13))
    last_month = int(df['date'].dt.month.max())
    default_idx = months.index(last_month) if last_month in months else 0
    month = st.selectbox('월 선택', months, index=default_idx)

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



# --- 맞춤 알림 ---
def render_alert(df: pd.DataFrame):
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

    color_map = {'[경고]':'red','[주의]':'orange','[주의 지속]':'red'}
    st.markdown(
        f"<span style='color:{color_map[level]}; font-weight:bold'>{level} 알림</span>",
        unsafe_allow_html=True
        )

    st.markdown(f"**{level} 알림**")
    for m in msgs:
        st.write(f"- {m}")
    if show_rec:
        st.markdown("<h3 style='text-align:left;'>✨ 추천 콘텐츠</h3>", unsafe_allow_html=True)
        st.write("- 오늘은 잠시 눈을 감고 깊게 숨을 쉬어볼까요?")
        st.write("- 좋아하는 음악 한 곡을 들어보세요.")



def build_dashboard_fig(df):
    mood      = df['category'].mode().iloc[0]
    score_map = {'부정':1, '중립':2, '긍정':3}
    val       = score_map[mood]
    emoji_map = {'부정':'☹️','중립':'😐','긍정':'😊'}
    ticks     = [emoji_map['부정'], emoji_map['중립'], emoji_map['긍정']]

    steps = []
    n_steps = 60
    for i, t in enumerate(np.linspace(0,1,n_steps)):
        r = int(255*(1-t)); g = int(255*t)
        pastel_r = int((r+255)/2); pastel_g = int((g+255)/2)
        color = f"rgba({pastel_r},{pastel_g},128,1)"
        start = 1 + (3-1)*i/n_steps
        end   = 1 + (3-1)*(i+1)/n_steps
        steps.append({'range':[start,end],'color':color})

    fig = go.Figure(go.Indicator(
        mode="gauge", value=val,
        gauge={
            'axis': {'range':[1,3],'tickmode':'array','tickvals':[1,2,3],'ticktext':ticks,'tickfont':{'size':30}},
            'bar':{'color':'black','thickness':0.2},
            'steps':steps,
            'threshold':{'line':{'color':'black','width':4},'thickness':0.8,'value':val}
        }
    ))
    fig.update_layout(
        title="▶ 감정 게이지",
        height=600, width=350, autosize=False,
        margin={'t':30,'b':10,'l':0,'r':0},
        annotations=[dict(x=1.5,y=-0.15,xref='x',yref='paper',
                          text="감정 게이지",showarrow=False,font={'size':20,'color':'#666'})]
    )
    return fig

def build_trend_fig(df):
    # render_trend 내부에서 fig 생성 부분만 옮겨서 반환
    import plotly.express as px
    # 날짜 필터링 없이 전체 기간 차트 그리기 로직 예시
    agg = df.groupby([df['date'].dt.date, 'emotion']).size().reset_index(name='count')
    pivot = agg.pivot(index='date', columns='emotion', values='count').fillna(0)
    ratio = pivot.div(pivot.sum(axis=1), axis=0).reset_index().melt(
        id_vars='date', var_name='emotion', value_name='ratio'
    )
    fig = px.line(ratio, x='date', y='ratio', color='emotion', markers=True,
                  labels={'date':'기간','ratio':'비율'}, title='▶ 감정 흐름')
    fig.update_yaxes(tickformat=".0%")
    return fig

def build_calendar_fig(df):
    # render_calendar 로직에서 테이블 대신 캘린더 차트를 그려주는 간단한 예시
    import plotly.figure_factory as ff
    dates = df['date'].dt.date
    fig = ff.create_gantt([{'Task': str(d), 'Start': d, 'Finish': d} for d in dates])
    return fig

def build_alert_fig(df):
    # render_alert 내부 로직을 재활용해서 간단한 막대그래프로 빈도 표시
    daily = df.groupby(df['date'].dt.date)['category'] \
              .apply(lambda s:(s=='부정').mean()) \
              .reset_index(name='neg_ratio')
    import plotly.express as px
    fig = px.bar(daily, x='date', y='neg_ratio',
                 title='▶ 부정 감정 비율 알림', labels={'neg_ratio':'부정 비율','date':'날짜'})
    return fig