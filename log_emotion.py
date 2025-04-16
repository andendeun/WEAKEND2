from backend.db import save_message

def log_emotion(username, emotion, message):
    # 감정 라벨을 포함해서 저장
    formatted_message = f"[{emotion}] {message}"
    save_message(username, "user", formatted_message)
