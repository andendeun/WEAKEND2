import torch
from transformers import AutoModel, AutoTokenizer
from model import EmotionClassifier
from dataset import EmotionDataset

def load_model(model_name, label_level):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 사전학습 모델 지정
    if model_name == "kcbert":
        pretrained = "beomi/kcbert-base"
    elif model_name == "koelectra":
        pretrained = "monologg/koelectra-base-discriminator"
    elif model_name == "klue":
        pretrained = "klue/roberta-base"
    else:
        raise ValueError("지원되지 않는 모델입니다.")

    # 토크나이저 및 base model 로드
    tokenizer = AutoTokenizer.from_pretrained(pretrained)
    base_model = AutoModel.from_pretrained(pretrained)

    # 레이블 수 추출을 위해 임시 데이터셋 로드
    dummy_dataset = EmotionDataset(
        csv_path="D:/workspace/Project_test/data/sample1.csv",
        levels=[label_level],
        model_name=model_name,
        tokenizer=tokenizer
    )
    label_mapping = dummy_dataset.label_mappings[label_level]
    id2label = {v: k for k, v in label_mapping.items()}
    num_labels = len(label_mapping)

    # 모델 생성 및 체크포인트 로딩
    model = EmotionClassifier(base_model, hidden_size=768, num_labels=num_labels)
    checkpoint_path = f"./checkpoints/{model_name}_{label_level}/model.pt"
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval()

    return model, tokenizer, id2label, device

def predict(text, model, tokenizer, id2label, device):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
    with torch.no_grad():
        probs = model(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
    pred_id = torch.argmax(probs, dim=1).item()
    pred_label = id2label[pred_id]
    return pred_label, probs.squeeze().tolist()

if __name__ == "__main__":
    input_text = "요즘 너무 지치고 힘들어."  # 예시 문장
    models = ["kcbert", "koelectra", "klue"]
    levels = ["대분류", "중분류", "소분류"]

    print(f"\n🔍 입력 문장: {input_text}")
    print(f"🧪 총 조합: {len(models)} 모델 × {len(levels)} 감정 레벨\n")

    for model_name in models:
        print(f"\n🧠 모델: {model_name.upper()}")
        for label_level in levels:
            try:
                model, tokenizer, id2label, device = load_model(model_name, label_level)
                label, probs = predict(input_text, model, tokenizer, id2label, device)
                print(f"  - [{label_level}] 예측 감정: {label} | Top Score: {max(probs):.4f}")
            except Exception as e:
                print(f"  - [{label_level}] ❌ 실패 ({e})")
