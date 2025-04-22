import os
import torch
import gdown
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification

@st.cache_resource
def load_model_and_tokenizer_from_drive(
    file_id: str,
    model_name: str = 'monologg/koelectra-base-discriminator',
    num_labels: int = 8
):
    """
    1) Google Drive에서 fine-tuned .pt 모델 파일을 내려받고
    2) HF Hub에서 AutoTokenizer 및 AutoModelForSequenceClassification을 로드
    3) 내려받은 state_dict를 model에 덮어씌움
    Drive 다운로드 실패 시 경고 후 허브에서만 로드
    """
    dest_dir  = "models"
    dest_path = os.path.join(dest_dir, "koelectra_emotion.pt")
    os.makedirs(dest_dir, exist_ok=True)

    # 1) Drive에서 .pt 파일 다운로드 (실패해도 계속)
    if not os.path.exists(dest_path):
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            with st.spinner("📥 감정 모델 다운로드 중…"):
                gdown.download(url, dest_path, quiet=False)
        except Exception as e:
            st.warning(f"⚠️ 모델 다운로드 실패, 허브에서 불러옵니다: {e}")

    # 2) 토크나이저 로드 (허브 fetch)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 3) 베이스 모델 로드 (허브 fetch)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels
    )

    # 4) fine-tuned weights 덮어쓰기
    if os.path.exists(dest_path):
        try:
            state_dict = torch.load(dest_path, map_location='cpu')
            model.load_state_dict(state_dict)
        except Exception as e:
            st.warning(f"⚠️ fine‑tuned weights 적용 실패: {e}")

    model.eval()
    return model, tokenizer