import os
import json
import csv
import pandas as pd
from dataset import get_emotion_name

# ✅ Google Drive 공유 링크 → 다운로드용 링크로 변환
EXCEL_FILE_ID = "1_o7DRLRewzZfnRjKCexu-KNLfTFK8_gX"
EXCEL_URL = f"https://drive.google.com/uc?export=download&id={EXCEL_FILE_ID}"

# ✅ 매핑 저장 함수
def save_all_label_mappings():
    models = ["kcbert", "koelectra", "klue"]
    levels = ["대분류", "중분류", "소분류"]
    save_dir = "label_mappings"
    os.makedirs(save_dir, exist_ok=True)

    print("📂 매핑 저장 디렉토리 생성:", save_dir)

    # ✅ 엑셀 파일 읽기
    print("📥 Excel 데이터 다운로드 및 로딩 중...")
    df = pd.read_excel(EXCEL_URL)
    print("✅ Excel 로딩 완료")

    for model in models:
        print(f"\n🚀 모델 [{model}]의 레이블 매핑 생성 중...")
        for level in levels:
            if level not in df.columns:
                print(f"⚠️ {level} 컬럼 없음 - 스킵")
                continue

            unique_values = df[level].dropna().unique().tolist()

            mapping = {}
            for idx, raw_label in enumerate(unique_values):
                key = f"{level}{idx + 1}"
                corrected_label = get_emotion_name(level, raw_label)
                mapping[key] = {"label": corrected_label, "index": idx}

            save_path = os.path.join(save_dir, f"{model}_{level}_mapping.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {model}_{level}_mapping.json 저장 완료")

    print("\n🎉 전체 레이블 매핑 저장 완료!")

if __name__ == "__main__":
    save_all_label_mappings()
