import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report
import os
import matplotlib.font_manager as fm

# 폰트 다운로드 및 설정
font_dir = "./fonts"
font_path = os.path.join(font_dir, "malgun.ttf")
os.makedirs(font_dir, exist_ok=True)

if os.path.exists(font_path):
    fontprop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = fontprop.get_name()
    plt.rcParams["axes.unicode_minus"] = False
else:
    fontprop = None 


def plot_emotion_trend(login_id: str, start_date, end_date) -> plt.Figure | None:
    df = get_emotion_report(login_id)
    df["분석 날짜"] = pd.to_datetime(df["분석 날짜"]).dt.date
    df = df[(df["분석 날짜"] >= start_date) & (df["분석 날짜"] <= end_date)]

    if df.empty:
        return None  # 👉 빈 데이터면 None 리턴

    pivot = df.groupby(["분석 날짜", "감정 카테고리"]) \
              .size().unstack(fill_value=0)

    fig, ax = plt.subplots()

    if pivot.empty:
        return None  # 👉 unstack 결과도 비어 있으면 None 리턴

    pivot.plot(ax=ax)

    if fontprop:
        ax.set_title("감정별 일별 발화 빈도", fontproperties=fontprop)
        ax.set_xlabel("날짜", fontproperties=fontprop)
        ax.set_ylabel("건수", fontproperties=fontprop)
        ax.legend(title="감정 카테고리", title_fontproperties=fontprop)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: pd.to_datetime(x).strftime("%Y-%m-%d")))
        ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=True))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontproperties=fontprop)
        plt.setp(ax.xaxis.get_minorticklabels(), rotation=45, ha="right", fontproperties=fontprop)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontproperties=fontprop)
        plt.setp(ax.get_yticklabels(), fontproperties=fontprop)
        plt.setp(ax.get_xticklabels(), fontproperties=fontprop)
        plt.setp(ax.get_yticklabels(), fontproperties=fontprop)
    else:
        ax.set_title("감정별 일별 발화 빈도")
        ax.set_xlabel("날짜")
        ax.set_ylabel("건수")

    plt.tight_layout()
    return fig
