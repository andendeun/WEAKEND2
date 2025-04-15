import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

def plot_emotion_trend(user_id):
    conn = sqlite3.connect("db/conversation.db")
    df = pd.read_sql(f"SELECT * FROM conversations WHERE user_id='{user_id}'", conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    emotion_counts = df.resample('1D')['emotion'].value_counts().unstack().fillna(0)
    emotion_counts.plot(kind='line', figsize=(12, 5))
    plt.title(f"감정 변화 추이 - {user_id}")
    plt.xlabel("날짜")
    plt.ylabel("감정 빈도")
    plt.legend(title="감정")
    plt.tight_layout()
    plt.savefig(f"reports/{user_id}_emotion_trend.png")
    plt.close()
