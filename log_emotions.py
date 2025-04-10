import os
import json
import csv
import requests
from datetime import datetime
from model import EnsembleEmotionModel

# ✅ Google Drive 파일 ID (샘플 매핑 파일 ID들 필요)
LABEL_MAPPING_IDS = {
    "kcbert_대분류": "1LQkaLx9kQqM7kSX8Eo3fF_QrXuUbO-5v",
    "kcbert_중분류": "1JnaQ7UNc4nI6llgC8O8eOXyC4jUtrN32",
    "kcbert_소분류": "1eIGxmqXVCmHnBKwSGZ6XI06suBUgK2VL",
    "klue_대분류": "1SOqFkr0s-8JcLKmq_p3YP1P9KS_AjBWa",
    "klue_중분류": "1Tq-f2o1SCbic8ghqoK5UAceMkE7E3miL",
    "klue_소분류": "1maz-9TnlNZKoUxBihDKzPM6Xl8-tQzUu",
    "koelectra_대분류": "1EG5d88pbUE-1v6mE8DIpiex_n2gvfPg8",
    "koelectra_중분류": "1Cwu8FfsqvVs454TZTkVq5ij04AofB1Wg",
    "koelectra_소분류": "1jmO3IPBUAgBswY71avy4KyWn1iEhlu5J",
}

LOG_PATH = "logs/emotion_log.csv"
MAPPING_DIR = "label_mappings"

# ✅ Google Drive 파일 다운로드 함수
def download_json_from_drive(file_id, destination_path):
    if not os.path.exists(destination_path):
        print(f"📥 {destination_path} 다운로드 중...")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 다운로드 완료")
    else:
        print(f"✅ {destination_path} 이미 존재")

# 🔄 label mapping 로드 함수
def load_label_mapping(model_name, level):
    key = f"{model_name}_{level}"
    file_id = LABEL_MAPPING_IDS.get(key)
    if not file_id:
        raise ValueError(f"❌ 매핑 ID가 등록되지 않았습니다: {key}")

    local_path = f"{MAPPING_DIR}/{key}_mapping.json"
    download_json_from_drive(file_id, local_path)

    with open(local_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    inverse = {}
    for k, v in mapping.items():
        if isinstance(v, dict) and "index" in v and "label" in v:
            inverse[str(v["index"])] = v["label"]
        else:
            inverse[str(v)] = k
    return inverse

# 🔍 감정 추론 및 로그 저장 함수
def log_emotion(input_text):
    label_counts = {
        "대분류": 4,
        "중분류": 10,
        "소분류": 42
    }

    model = EnsembleEmotionModel(num_labels_dict=label_counts)
    predictions = model.predict(input_text)

    result_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_text": input_text
    }

    for model_name, levels in predictions.items():
        for level, probs in levels.items():
            top_idx = probs.argmax().item()
            top_prob = probs[top_idx].item()
            inv_map = load_label_mapping(model_name, level)
            label_name = inv_map.get(str(top_idx), f"알 수 없음({top_idx})")
            result_row[f"{model_name.upper()}_{level}"] = f"{label_name}({top_prob:.2f})"

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
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
