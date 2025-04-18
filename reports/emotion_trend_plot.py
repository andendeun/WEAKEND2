import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report
import os
import gdown
import matplotlib.font_manager as fm

# 폰트 다운로드 및 설정
font_dir = "./fonts"
font_path = os.path.join(font_dir, "malgun.ttf")
os.makedirs(font_dir, exist_ok=True)

if not os.path.exists(font_path):
    gdown.download(
        "https://drive.google.com/uc?id=17YAJTJCyK1ZILSY2n1luosc-uHOCTp-b", 
        font_path,
        quiet=False
    )

# matplotlib에 적용
if os.path.exists(font_path):
    fontprop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = fontprop.get_name()
    plt.rcParams["axes.unicode_minus"] = False

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