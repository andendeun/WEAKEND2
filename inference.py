from utils.load_model_from_drive import load_model_and_tokenizer_from_drive
import torch

FILE_ID = "1k5UxaYqj3ExEJUxwRBiDatHYYGRYJN31"  # Google Drive 공유 링크에서 추출한 ID
model, tokenizer = load_model_and_tokenizer_from_drive(FILE_ID)

labels = [
    "행복/기쁨/감사",
    "신뢰/편안/존경/안정",
    "분노/짜증/불편",
    "당황/충격/배신감",
    "공포/불안",
    "고독/외로움/소외감/허탈",
    "죄책감/미안함",
    "걱정/고민/긴장"
]

def predict_emotion(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        pred = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred].item()
    return labels[pred], confidence
