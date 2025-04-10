import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm

# ✅ Google Drive 파일 ID (emotion_log.csv)
LOG_FILE_ID = "1C9fS-Dvhxhq2oKEATwXX0gwjMhBQONpA"
csv_path = "logs/emotion_log.csv"

# ✅ Google Drive 파일 다운로드 함수
def download_csv_from_drive(file_id, destination_path):
    if not os.path.exists(destination_path):
        print(f"📥 CSV 다운로드 중: {destination_path}")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 다운로드 완료")
    else:
        print("✅ CSV 이미 존재")

# ✅ 감정 흐름 분석 및 시각화 함수
def generate_emotion_plot():
    # CSV 다운로드
    download_csv_from_drive(LOG_FILE_ID, csv_path)

    # 한글 폰트 설정 (Windows 기준)
    font_path = "C:/Windows/Fonts/malgun.ttf"
    if os.path.exists(font_path):
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
    else:
        print("⚠️ 한글 폰트 파일을 찾을 수 없습니다. 기본 폰트로 출력됩니다.")

    # 데이터 불러오기
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # 모델 및 레벨 리스트
    models = ["KCBERT", "KOELECTRA", "KLUE"]
    levels = ["대분류", "중분류", "소분류"]

    # 감정 흐름 시각화
    for model in models:
        for level in levels:
            col = f"{model}_{level}"
            if col not in df.columns:
                continue
            df[f"{col}_감정명"] = df[col].apply(lambda x: x.split("(")[0] if isinstance(x, str) else x)

            plt.figure(figsize=(12, 4))
            sns.lineplot(data=df, x="timestamp", y=f"{col}_감정명", marker="o")
            plt.title(f"📈 감정 흐름 - {col}")
            plt.xlabel("시간")
            plt.ylabel("감정")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.show()

    # 텍스트 기반 분석 요약
    print("\n📝 텍스트 기반 감정 분석 요약:")
    for model in models:
        for level in levels:
            col = f"{model}_{level}"
            if col in df.columns:
                most_common = df[col].apply(lambda x: x.split("(")[0] if isinstance(x, str) else x).value_counts().idxmax()
                print(f"  - {col}: 가장 자주 등장한 감정 → {most_common}")
