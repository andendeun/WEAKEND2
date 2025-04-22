import os
import torch
import gdown
import streamlit as st
from transformers import ElectraForSequenceClassification, ElectraTokenizer

@st.cache_resource
def load_model_and_tokenizer_from_drive(
    file_id: str,
    model_name: str = 'monologg/koelectra-base-discriminator',
    num_labels: int = 8
):
    """
    1) 구글 드라이브에서 pt 파일을 내려받고
    2) HF 토크나이저 및 베이스 모델 로드
    3) pt state_dict 덮어쓰기
    실패시 모두 허깅페이스 허브에서만 불러오도록 폴백 처리
    """
    dest_dir  = "models"
    dest_path = os.path.join(dest_dir, "koelectra_emotion.pt")
    os.makedirs(dest_dir, exist_ok=True)

    # ————————————
    # 1) Drive에서 다운로드 (실패해도 계속)
    # ————————————
    if not os.path.exists(dest_path):
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            with st.spinner("📥 감정 모델 다운로드 중…"):
                gdown.download(url, dest_path, quiet=False)
        except Exception as e:
            st.warning(f"⚠️ 모델 다운로드 실패, 허브에서 불러옵니다: {e}")

    # ————————————
    # 2) 토크나이저 & 베이스 모델
    # ————————————
    tokenizer = None
    model     = None
    try:
        tokenizer = ElectraTokenizer.from_pretrained(model_name)
    except Exception as e:
        st.error(f"❌ 토크나이저 로드 실패: {e}")
        raise

    try:
        model = ElectraForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels
        )
    except Exception as e:
        st.warning(f"⚠️ 베이스 모델 로드 실패 ({model_name}), 로컬 파일만 시도합니다: {e}")
        model = ElectraForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            local_files_only=True
        )

    # ————————————
    # 3) pt state_dict 덮어쓰기 (없거나 실패 시 무시)
    # ————————————
    if os.path.exists(dest_path):
        try:
            state = torch.load(dest_path, map_location='cpu')
            model.load_state_dict(state)
        except Exception as e:
            st.warning(f"⚠️ fine‑tuned weights 적용 실패: {e}")

    model.eval()
    return model, tokenizer
