import os
import pandas as pd
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import requests
load_dotenv()

# ✅ 환경변수로 OpenAI API 키 불러오기
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Google Drive 파일 ID
LOG_FILE_ID = "1num0DWWm10m0_AB468pJubvk3oi0i_xK"
log_path = "logs/emotion_log.csv"
feedback_path = "logs/gpt_feedback_log.csv"

def download_csv_from_drive(file_id, destination_path):
    if not os.path.exists(destination_path):
        print(f"📥 {destination_path} 다운로드 중...")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 다운로드 완료")
    else:
        print(f"✅ {destination_path} 이미 존재")

# ✅ 다운로드 실행
download_csv_from_drive(LOG_FILE_ID, log_path)

# ✅ GPT 프롬프트 생성 함수
def create_prompt(row):
    return f"""
[1] 세 모델(KCBERT, KOELECTRA, KLUE)의 감정 분석 결과를 검토하고 보완해줘.
→ 서로 다른 결과가 있는 경우 더 신뢰도 높고 맥락에 맞는 감정으로 통합해줘.

문장: "{row['input_text']}"

KCBERT 분석 결과:
  - 대분류: {row['KCBERT_대분류']}
  - 중분류: {row['KCBERT_중분류']}
  - 소분류: {row['KCBERT_소분류']}

KOELECTRA 분석 결과:
  - 대분류: {row['KOELECTRA_대분류']}
  - 중분류: {row['KOELECTRA_중분류']}
  - 소분류: {row['KOELECTRA_소분류']}

KLUE 분석 결과:
  - 대분류: {row['KLUE_대분류']}
  - 중분류: {row['KLUE_중분류']}
  - 소분류: {row['KLUE_소분류']}

이제 아래 지침에 따라 응답을 작성해줘:

[Admin Only]
세 모델의 감정 결과를 비교·검토하여 더 적절한 감정을 판단하고, 
필요시 보완해줘. 보완된 감정을 대·중·소 분류 형태로 
두괄식 개조식으로 리포트형태로 정리해줘. 그리고 해당하는 유저에게
필요한 대처는 무엇일지 판단해서 간단하게 기록해줘.
그리고 유저식별코드와 감정이 기록된 날짜(숫자,로그)도 포함해줘(이모티콘을 사용해서 정리)

[User Only]
보완된 감정 결과를 기반으로 아래 항목을 작성해줘:
1. 감정 상태 요약 (한 문단)
2. 공감적이고 따뜻한 위로의 말
3. 실천 가능한 행동 제안

답변은 공감적이고 적합한 이모티콘을 사용한 가독성있는 
부드러운 문체로 작성해줘.
"""

# ✅ GPT 응답 요청 함수
def generate_feedback(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 감정 케어 전문 심리 분석가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1200
    )
    return response.choices[0].message.content.strip()

# ✅ 응답 분리 함수
def split_feedback(response_text):
    admin_note = ""
    user_note = ""
    if "[Admin Only]" in response_text and "[User Only]" in response_text:
        parts = response_text.split("[User Only]")
        admin_note = parts[0].replace("[Admin Only]", "").strip()
        user_note = parts[1].strip()
    else:
        user_note = response_text.strip()
    return admin_note, user_note

# ✅ 전체 실행용
def run_gpt_feedback():
    df = pd.read_csv(log_path)
    latest = df.tail(1).iloc[0]

    prompt = create_prompt(latest)
    print("\n📤 GPT 요청 프롬프트 생성 완료!")

    response_text = generate_feedback(prompt)
    print("\n📥 GPT 응답 수신 완료!")

    admin_note, user_note = split_feedback(response_text)

    feedback_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_text": latest['input_text'],
        "admin_feedback": admin_note,
        "user_feedback": user_note
    }

    if os.path.exists(feedback_path):
        pd.DataFrame([feedback_entry]).to_csv(feedback_path, mode='a', index=False, header=False)
    else:
        pd.DataFrame([feedback_entry]).to_csv(feedback_path, index=False)

    print("\n✅ GPT 감정 피드백 저장 완료!")
    print("\n📘 [User 전용 피드백]\n")
    print(user_note)
    print("\n🔐 [Admin 참고용 분석]\n")
    print(admin_note)

# ✅ Streamlit 앱에서 사용할 함수
def get_gpt_feedback(row: dict) -> str:
    prompt = create_prompt(row)
    response = generate_feedback(prompt)
    _, user_note = split_feedback(response)
    return user_note

if __name__ == "__main__":
    run_gpt_feedback()