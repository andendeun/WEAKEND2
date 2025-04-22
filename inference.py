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
    "슬픔",
    "소외",
    "분노",
    "불안",
    "긍정",
    "중립",
    "당황",
    "위협"
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
