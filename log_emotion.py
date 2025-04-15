from backend.db import init_db

def log_emotion(username, emotion, message):
    # 감정 라벨을 포함해서 저장
    formatted_message = f"[{emotion}] {message}"
    init_db(username, "user", formatted_message)
