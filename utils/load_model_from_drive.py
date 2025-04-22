import os
import torch
import gdown
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification

@st.cache_resource
def load_model_and_tokenizer_from_drive(
    file_id: str,
    model_name: str = 'monologg/koelectra-base-discriminator',
    num_labels: int = 8,
    tokenizer_folder_id: str = None
):
    """
    1) Google Drive에서 fine-tuned .pt 모델 파일 다운로드
    2) (선택) Drive에서 tokenizer 파일 폴더 다운로드
    3) tokenizer와 base 모델 로드 (local first, then hub)
    4) fine-tuned weights 덮어쓰기
    """
    dest_dir    = "models"
    os.makedirs(dest_dir, exist_ok=True)
    # -- weights --
    pt_path     = os.path.join(dest_dir, "koelectra_emotion.pt")
    if not os.path.exists(pt_path):
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            with st.spinner("📥 모델 파일 다운로드 중..."):
                gdown.download(url, pt_path, quiet=False)
        except Exception as e:
            st.error(f"모델 다운로드 실패: {e}")
            raise
    # -- tokenizer files --
    tok_dir = os.path.join(dest_dir, "tokenizer")
    if tokenizer_folder_id and not os.path.exists(tok_dir):
        try:
            # Drive 폴더 전체 다운로드
            url = f"https://drive.google.com/drive/folders/{tokenizer_folder_id}"
            with st.spinner("📥 토크나이저 다운로드 중..."):
                gdown.download_folder(url, output=tok_dir)
        except Exception as e:
            st.warning(f"토크나이저 다운로드 실패, 허브 시도: {e}")
    # -- tokenizer load --
    try:
        if os.path.exists(tok_dir):
            tokenizer = AutoTokenizer.from_pretrained(tok_dir, local_files_only=True)
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
    except Exception as e:
        st.error(f"토크나이저 로드 실패: {e}")
        raise
    # -- base model load --
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=num_labels
        )
    except Exception:
        st.warning("허브 연결 실패, local only 로드 시도")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=num_labels, local_files_only=True
        )
    # -- weights apply --
    try:
        state = torch.load(pt_path, map_location='cpu')
        model.load_state_dict(state)
    except Exception as e:
        st.warning(f"fine-tuned weights 적용 실패: {e}")
    model.eval()
    return model, tokenizer
