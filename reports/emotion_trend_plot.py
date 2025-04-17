import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report

def plot_emotion_trend(login_id: str, start_date, end_date) -> plt.Figure:
    df = get_emotion_report(login_id)
    df["분석 날짜"] = pd.to_datetime(df["분석 날짜"]).dt.date
    df = df[(df["분석 날짜"] >= start_date) & (df["분석 날짜"] <= end_date)]
    pivot = df.groupby(["분석 날짜", "감정 카테고리"]) \
              .size().unstack(fill_value=0)

    fig, ax = plt.subplots()
    pivot.plot(ax=ax)
    ax.set_title("감정별 일별 발화 빈도")
    ax.set_xlabel("날짜")
    ax.set_ylabel("건수")
    plt.tight_layout()
    return fig