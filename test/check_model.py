import torch
from transformers import ElectraTokenizer, ElectraForSequenceClassification
import torch.nn.functional as F

# 설정
MODEL_PATH = "koelectra_emotion.pt"
NUM_LABELS = 8

label_list = [
    "행복/기쁨/감사",
    "신뢰/편안/존경/안정",
    "분노/짜증/불편",
    "당황/충격/배신감",
    "공포/불안",
    "고독/외로움/소외감/허탈",
    "죄책감/미안함",
    "걱정/고민/긴장"
]

# 모델 & 토크나이저 로딩
tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-discriminator")
model = ElectraForSequenceClassification.from_pretrained(
    "monologg/koelectra-base-discriminator", num_labels=NUM_LABELS
)
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

# 예측 함수 (확률 포함)
def predict_emotion(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1).squeeze()
        pred_idx = torch.argmax(probs).item()
        confidence = probs[pred_idx].item()
        
    return label_list[pred_idx], confidence, probs

# 테스트 문장 리스트
texts = [
    "오늘 하루 너무 외롭고 허탈해",
    "정말 감사한 마음이 들어",
    "걔는 나한테 배신감을 줬어",
    "속이 너무 불안하고 초조해",
    "짜증나고 화가 나"
]

# 실행
print("\n📌 예측 테스트 시작:")
for text in texts:
    label, confidence, prob_tensor = predict_emotion(text)
    print(f"🗣 \"{text}\"")
    print(f"🔮 예측: {label} ({confidence:.2%} 확률)\n")
