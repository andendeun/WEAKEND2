from utils.load_model_from_drive import load_model_and_tokenizer_from_drive
import torch
import torch.nn.functional as F

# Google Drive 파일 ID
FILE_ID = "1nCl-o_k9u2zcPT4sMcDsUlP1Y66VJaOw"

model, tokenizer = load_model_and_tokenizer_from_drive(
    FILE_ID, 
    model_name='monologg/koelectra-base-discriminator', 
    num_labels=8
)

# 감정 라벨 (8개)
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


def predict_emotion_with_score(text: str) -> tuple[str, float]:
    """
    문장의 가장 높은 클래스 라벨과 그 확률을 출력
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)[0] 
        score, idx = torch.max(probs, dim=0)
    return label_list[idx.item()], score.item()
