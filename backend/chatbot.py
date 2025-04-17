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
당신은 따뜻하고 신뢰할 수 있는 감정 상담사입니다. 
사용자가 처한 문제 상황을 한 번 더 요약해서 제공하고, 어떤 기분이었는지 물어보세요.
또한, 사용자가 감정 단어를 표현할 수 있도록 질문을 통해 유도하세요.
3000자 이내로 답변하세요.
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
        model="gpt-3.5-turbo-16k",
        messages=prompt_messages,
    )

    # 4) 모델 답변을 히스토리에 추가
    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    return reply