import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report
import os
import matplotlib.font_manager as fm


# 한글폰트 설정
font_dir = "./fonts"
font_path = os.path.join(font_dir, "malgun.ttf")
os.makedirs(font_dir, exist_ok=True)
if os.path.exists(font_path):
    fontprop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = fontprop.get_name()
    plt.rcParams["axes.unicode_minus"] = False
else:
    fontprop = None

label_list = [
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
    df = get_emotion_report(login_id)
    df["분석 날짜"] = pd.to_datetime(df["분석 날짜"])
    mask = (
        (df["분석 날짜"].dt.date >= start_date) &
        (df["분석 날짜"].dt.date <= end_date)
    )
    df = df.loc[mask]
    if df.empty:
        return None

    # 리샘플링 주기 설정
    freq = {"일별": "D", "주별": "W-MON", "월별": "M"}[period]

    # 그룹화 & 건수 계산
    df = df.set_index("분석 날짜")
    grp = df.groupby([pd.Grouper(freq=freq), "감정 카테고리"]).size()
    emotion_per_period = grp.reset_index(name="건수")
    total_per_period = (
        emotion_per_period
        .groupby("분석 날짜")["건수"]
        .sum()
        .reset_index(name="총합")
    )
    merged = pd.merge(emotion_per_period, total_per_period, on="분석 날짜")
    merged["비율"] = merged["건수"] / merged["총합"] * 100

    # 피벗 & 없는 라벨은 0으로 채우기
    pivot = (
        merged
        .pivot(index="분석 날짜", columns="감정 카테고리", values="비율")
        .reindex(columns=label_list, fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(6, 12))
    pivot.plot(ax=ax, legend=False)

    # 범례
    num_cols = 2  # 한 행
    props = dict(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=num_cols,
        frameon=False
    )
    if fontprop:
        ax.legend(label_list, prop=fontprop, **props)
    else:
        ax.legend(label_list, **props)

    # x축 포맷
    fmt = {"일별": "%m/%d", "주별": "%y-%m-%d", "월별": "%Y-%m"}[period]
    ax.set_xticks(pivot.index)
    ax.set_xticklabels([d.strftime(fmt) for d in pivot.index], rotation=0)

    # y축 및 (%) 표시
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylim(0, 100)
    ax.annotate(
        "(%)",
        xy=(0.01, 1.02),
        xycoords="axes fraction",
        ha="left",
        va="bottom"
    )

    plt.tight_layout(pad=2.0)
    return fig