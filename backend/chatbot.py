import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# DB 저장 함수 가져오기
from backend.db import save_message

# 시스템 프롬프트: 상담사 역할
system_prompt = """
너는 감정을 잘 이해하고 따뜻하게 반응하는 감성 챗봇이야. 
사용자가 보낸 메시지에 담긴 감정을 읽고, 짧고 진심 어린 말투로 공감해줘.  
답변은 너무 길지 않게, 친구에게 말하듯 1~2문장 정도로 말해줘. 
해결책을 제시하는 대신, 감정에 공감하는 말을 해줘.
사용자가 스스로를 자책하지 않도록, 말투는 조심스럽고 부드럽게 해줘.
대화를 종결하는 대신, 사용자가 계속 이야기할 수 있도록 대화해줘.
"""

# 대화 기록 초기화
chat_history: list[ChatCompletionMessageParam] = [
    {"role": "system", "content": system_prompt}
]

def generate_response(user_input: str) -> str:
    # 1) 유저 메시지를 히스토리에 추가
    chat_history.append({"role": "user", "content": user_input})

    # 2) 토큰 폭주 방지: 시스템 + 최근 10턴만 남기기
    MAX_TURNS = 10
    system = chat_history[0]
    history = chat_history[1:]
    trimmed = history[-MAX_TURNS*2:]   # user+assistant 합쳐 2개 per turn
    prompt_messages = [system] + trimmed

    # 3) OpenAI API 호출 (trimmed 히스토리만 전달)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt_messages,
    )

    # 4) 모델 답변을 히스토리에 추가
    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    return reply