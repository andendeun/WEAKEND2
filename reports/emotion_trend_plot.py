import os
import pandas as pd
import matplotlib as mpl
import matplotlib.font_manager as fm

# ────────────────────────────────────────────────────────────────────────────────
# 1) (Colab 전용) Google Drive 마운트
try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=True)
    DRIVE_MOUNTED = True
except ImportError:
    DRIVE_MOUNTED = False

# 2) 폰트 경로 설정
if DRIVE_MOUNTED:
    FONT_PATH = '/content/drive/MyDrive/fonts/malgun.ttf'
else:
    FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'malgun.ttf')

# 3) Matplotlib에 한글폰트 등록 (pyplot import 전)
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    FONT_NAME = fm.FontProperties(fname=FONT_PATH).get_name()
    mpl.rcParams['font.family'] = FONT_NAME
    mpl.rcParams['axes.unicode_minus'] = False
else:
    print(f"[경고] 한글 폰트 파일을 찾을 수 없습니다: {FONT_PATH}")

# pyplot은 폰트 설정 이후에 import
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report

# ────────────────────────────────────────────────────────────────────────────────
# 감정 카테고리 순서 정의
LABEL_LIST = [
    "행복/기쁨/감사",
    "신뢰/편안/존경/안정",
    "분노/짜증/불편",
    "당황/충격/배신감",
    "공포/불안",
    "고독/외로움/소외감/허탈",
    "죄책감/미안함",
    "걱정/고민/긴장"
]

def plot_emotion_trend(
    login_id: str,
    start_date,
    end_date,
    period: str = "일별"
) -> plt.Figure | None:
    """
    사용자의 감정 리포트를 불러와서 기간별(일/주/월) 감정 비율 트렌드 차트를 그리는 함수.
    - login_id: 사용자 아이디
    - start_date, end_date: datetime.date 혹은 문자열(ISO) 형태
    - period: "일별", "주별", "월별"
    """
    # 데이터 로드
    df = get_emotion_report(login_id)
    if df.empty:
        return None

    # 날짜 컬럼 변환 & 필터링
    df['분석 날짜'] = pd.to_datetime(df['분석 날짜'])
    mask = (
        (df['분석 날짜'].dt.date >= pd.to_datetime(start_date).date()) &
        (df['분석 날짜'].dt.date <= pd.to_datetime(end_date).date())
    )
    df = df.loc[mask]
    if df.empty:
        return None

    # 리샘플링 주기 맵핑
    freq_map = {"일별": "D", "주별": "W-MON", "월별": "M"}
    freq = freq_map.get(period, "D")

    # 인덱스 설정 후 그룹화
    df = df.set_index('분석 날짜')
    grp = df.groupby([pd.Grouper(freq=freq), '감정 카테고리']).size()
    emotion_per_period = grp.reset_index(name='건수')

    # 총합 계산
    total_per_period = (
        emotion_per_period
        .groupby('분석 날짜')['건수']
        .sum()
        .reset_index(name='총합')
    )

    # 병합 & 비율 계산
    merged = pd.merge(emotion_per_period, total_per_period, on='분석 날짜')
    merged['비율'] = merged['건수'] / merged['총합'] * 100

    # 피벗 테이블 생성, 없는 라벨은 0으로 채움
    pivot = (
        merged
        .pivot(index='분석 날짜', columns='감정 카테고리', values='비율')
        .reindex(columns=LABEL_LIST, fill_value=0)
    )

    # ─── 차트 그리기 ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 6))
    pivot.plot(ax=ax, legend=False)

    # 범례 설정 (2열)
    legend_props = dict(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=False
    )
    legend_font = fm.FontProperties(fname=FONT_PATH) if os.path.exists(FONT_PATH) else None
    ax.legend(LABEL_LIST, prop=legend_font, **legend_props)

    # X축 레이블 포맷 설정
    fmt_map = {"일별": "%m/%d", "주별": "%y-%m-%d", "월별": "%Y-%m"}
    fmt = fmt_map.get(period, "%m/%d")
    ax.set_xticks(pivot.index)
    ax.set_xticklabels([d.strftime(fmt) for d in pivot.index], rotation=0)

    # Y축 (0~100%) 설정 및 (%) 표시
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylim(0, 100)
    ax.annotate('(%)', xy=(0.01, 1.02), xycoords='axes fraction',
                ha='left', va='bottom')

    plt.tight_layout(pad=2.0)
    return fig