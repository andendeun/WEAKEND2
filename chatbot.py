import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 시스템 프롬프트: 상담사 역할
system_prompt = """
당신은 따뜻하고 신뢰할 수 있는 감정 상담사입니다.
사용자가 현재 어떤 감정을 느끼고 있는지를 이해하고, 나이/성별/배경/문제 상황/니즈 등의 정보를 자연스럽게 질문을 통해 파악해 주세요.
공감 중심의 대화를 유지하며, 무리한 질문은 피하고 감정을 배려하는 말투를 사용하세요.
"""

# 대화 기록 초기화
chat_history: list[ChatCompletionMessageParam] = [
    {"role": "system", "content": system_prompt}
]

def generate_response(user_input: str) -> str:
    chat_history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_history
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})
    return reply

