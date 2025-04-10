import os
import json
import csv

def get_emotion_name(level, raw_value):
    """
    미리 정의한 감정명 사전을 통해, CSV에서 읽어온 값(raw_value)을 변환합니다.
    
    예시:
      - "대분류1" -> "슬픔"
      - "대분류2" -> "분노"
      - "대분류3" -> "놀람"
      - "대분류4" -> "기쁨"
    
    중분류와 소분류도 필요에 따라 추가하세요.
    """
    predefined = {
        "대분류": {
            "대분류1": "슬픔",
            "대분류2": "분노",
            "대분류3": "놀람",
            "대분류4": "기쁨"
        },
        "중분류": {
            "중분류1": "우울",
            "중분류2": "절망",
            "중분류3": "분개",
            "중분류4": "경악",
            "중분류5": "상실",
            "중분류6": "당황",
            "중분류7": "흥분",
            "중분류8": "편안",
            "중분류9": "감사",
            "중분류10": "사랑"
        },
        "소분류": {
            # 예시로 몇 개만 채워봅니다. 실제 사용에 맞게 채워주세요.
            "소분류1": "비통",
            "소분류2": "시무룩",
            "소분류3": "격노",
            "소분류4": "분개",
            "소분류5": "경악",
            "소분류6": "낙담",
            "소분류7": "당황",
            "소분류8": "희열",
            "소분류9": "감동",
            "소분류10": "사랑"
            # ... 필요시 소분류 42까지 추가
        }
    }
    # 미리 정의된 값이 있으면 변환, 없으면 원본 사용
    return predefined.get(level, {}).get(raw_value, raw_value)

def save_all_label_mappings():
    csv_path = "D:/workspace/Project_test/data/sample1.csv"
    models = ["kcbert", "koelectra", "klue"]
    levels = ["대분류", "중분류", "소분류"]
    save_dir = "D:/workspace/Project/label_mappings"
    os.makedirs(save_dir, exist_ok=True)

    print("📂 매핑 저장 디렉토리 생성:", save_dir)

    # CSV 파일 읽기: 헤더를 기준으로 딕셔너리 형태로 저장
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for model in models:
        print(f"\n🚀 모델 [{model}]의 레이블 매핑 생성 중...")
        for level in levels:
            unique_values = []
            for row in rows:
                value = row.get(level)
                if value is None:
                    continue  # 해당 컬럼이 없으면 건너뜁니다.
                if value not in unique_values:
                    unique_values.append(value)
            # 각 고유 값에 대해 상세 정보 포함 매핑 생성  
            # key는 f"{level}{순번}" 형식, value는 { "label": 감정명, "index": 내부 인덱스 } 형식
            mapping = {}
            for idx, raw_label in enumerate(unique_values):
                key = f"{level}{idx + 1}"  # 순번은 1부터 시작
                # raw_label 값(예: "대분류4")를 미리 정의한 사전으로 변환
                corrected_label = get_emotion_name(level, raw_label)
                mapping[key] = {"label": corrected_label, "index": idx}

            save_path = os.path.join(save_dir, f"{model}_{level}_mapping.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {model}_{level}_mapping.json 저장 완료")
    
    print("\n🎉 전체 레이블 매핑 저장 완료!")

if __name__ == "__main__":
    save_all_label_mappings()
