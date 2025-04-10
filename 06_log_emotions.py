import os
import json
import csv
from datetime import datetime
from model import EnsembleEmotionModel

# 🔄 label mapping 로드 함수 (상세 정보 포함 버전)
def load_label_mapping(model_name, level):
    path = f"D:/workspace/Project/label_mappings/{model_name}_{level}_mapping.json"
    with open(path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    # 매핑 파일은 상세 정보를 포함합니다.
    # 예: { "대분류1": {"label": "기쁨", "index": 0}, ... }
    # 여기서 역매핑은 index값(문자열) -> 라벨명 ("기쁨")으로 생성합니다.
    inverse = {}
    for key, value in mapping.items():
        if isinstance(value, dict) and "index" in value and "label" in value:
            inverse[str(value["index"])] = value["label"]
        else:
            # 단순 매핑 형식일 경우 기존 방식 사용
            inverse[str(value)] = key
    return inverse

# 🔍 감정 추론 및 로그 저장 함수
def log_emotion(input_text):
    # ✅ 레이블 개수 사전 (각 분류 레벨별)
    label_counts = {
        "대분류": 4,
        "중분류": 10,
        "소분류": 42
    }

    # EnsembleEmotionModel은 num_labels_dict를 입력받습니다.
    model = EnsembleEmotionModel(num_labels_dict=label_counts)
    predictions = model.predict(input_text)

    result_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_text": input_text
    }

    # 예측 결과(딕셔너리)를 순회하며 각 모델/레벨별 최상위 인덱스와 확률 확인
    for model_name, levels in predictions.items():
        for level, probs in levels.items():
            top_idx = probs.argmax().item()
            top_prob = probs[top_idx].item()
            inv_map = load_label_mapping(model_name, level)
            try:
                label_name = inv_map[str(top_idx)]
            except KeyError:
                label_name = f"알 수 없음({top_idx})"
            result_row[f"{model_name.upper()}_{level}"] = f"{label_name}({top_prob:.2f})"

    # ✅ 로그 파일 저장
    log_path = "D:/workspace/Project/logs/emotion_log.csv"
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(result_row)

    print("✅ 감정 로그 저장 완료!")
    print(result_row)

# ✅ 실행부
if __name__ == "__main__":
    test_input = input("감정 입력 문장을 적어주세요: ")
    log_emotion(test_input)
