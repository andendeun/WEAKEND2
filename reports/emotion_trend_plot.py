# reports/emotion_trend_plot.py

import pandas as pd
import matplotlib.pyplot as plt
from .generate_report import get_emotion_report

def plot_emotion_trend(login_id: str, start_date, end_date) -> plt.Figure:
    df = get_emotion_report(login_id)
    # 이하 생략…
