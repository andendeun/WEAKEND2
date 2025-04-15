import torch
from transformers import ElectraTokenizer, ElectraForSequenceClassification
import torch.nn.functional as F

# 모델 불러오기
model_path = "koelectra_emotion.pt"
model = ElectraForSequenceClassification.from_pretrained("monologg/koelectra-base-discriminator", num_labels=8)
model.load_state_dict(torch.load(model_path, map_location="cpu"))
model.eval()

# 토크나이저
tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-discriminator")

# 라벨 리스트
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

# 예측 함수
def predict_emotion(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        return label_list[pred_idx]

# 테스트
sentence = "가끔 맛집 탐방을 사진과 함께 블로그에 정성껏 올리면 검색 유입이 늘어나고 소소한 광고 수익도 기대해볼 수 있어"
print("예측 감정:", predict_emotion(sentence))
