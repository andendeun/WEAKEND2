import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os

# ✅ 한글 폰트 설정 (윈도우 기준)
font_path = "C:/Windows/Fonts/malgun.ttf"
if os.path.exists(font_path):
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
else:
    print("❌ 한글 폰트 파일을 찾을 수 없습니다.")

# ✅ 로그 파일 경로
csv_path = "D:/workspace/Project/logs/emotion_log.csv"

# ✅ 데이터 불러오기
df = pd.read_csv(csv_path)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

# ✅ 모델 및 레벨 리스트
models = ["KCBERT", "KOELECTRA", "KLUE"]
levels = ["대분류", "중분류", "소분류"]

# ✅ 감정 흐름 시각화
for model in models:
    for level in levels:
        col = f"{model}_{level}"
        if col not in df.columns:
            continue
        df[f"{col}_감정명"] = df[col].apply(lambda x: x.split("(")[0])

        plt.figure(figsize=(12, 4))
        sns.lineplot(data=df, x="timestamp", y=f"{col}_감정명", marker="o")
        plt.title(f"📈 감정 흐름 - {col}")
        plt.xlabel("시간")
        plt.ylabel("감정")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# ✅ 텍스트 기반 분석 요약
print("\n📝 텍스트 기반 감정 분석 요약:")
for model in models:
    for level in levels:
        col = f"{model}_{level}"
        if col in df.columns:
            most_common = df[col].apply(lambda x: x.split("(")[0]).value_counts().idxmax()
            print(f"  - {col}: 가장 자주 등장한 감정 → {most_common}")
