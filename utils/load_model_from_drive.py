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
    1) Google Drive에서 fine-tuned .pt 모델 파일을 다운로드
    2) 로컬에 커밋된 tokenizer 폴더에서 토크나이저를 우선 로드, 실패 시 HF Hub fetch
    3) 허브에서 base 모델 불러오기
    4) fine-tuned 가중치 덮어씌우기
    """
    # 1) weights 파일
    dest_dir = "models"
    os.makedirs(dest_dir, exist_ok=True)
    weights_path = os.path.join(dest_dir, "koelectra_emotion.pt")
    if not os.path.exists(weights_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 감정 모델 다운로드 중…"):
            gdown.download(url, weights_path, quiet=False)

    # 2) tokenizer: 로컬 커밋 폴더 우선, 없으면 허브에서
    safe_name = model_name.replace("/", "_")
    tokenizer_dir = os.path.join(dest_dir, "tokenizers", safe_name)
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_dir,
            local_files_only=True
        )
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 3) base 모델 로드 (허브 fetch 필요)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels
    )

    # 4) fine-tuned weights 적용
    state_dict = torch.load(weights_path, map_location='cpu')
    model.load_state_dict(state_dict)
    model.eval()

    return model, tokenizer