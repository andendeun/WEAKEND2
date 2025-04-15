from utils.load_model_from_drive import load_model_and_tokenizer_from_drive
from backend.predict_text import predict_emotion

# Google Drive 파일 ID (너의 kcbert_max.pt 공유 링크에서 추출)
FFILE_ID = "1rl_QDbe7PR1BqNiflZE72GrIEtljBxZw"

# 모델 & 토크나이저 캐싱 로드
model, tokenizer = load_model_and_tokenizer_from_drive(FILE_ID)

def predict_emotion_from_text(text):
    return predict_emotion(text, model, tokenizer)
