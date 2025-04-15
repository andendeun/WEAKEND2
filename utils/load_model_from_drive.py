import os
import torch
import gdown
import streamlit as st
from transformers import AutoTokenizer, ElectraForSequenceClassification

@st.cache_resource
def load_model_and_tokenizer_from_drive(file_id, model_name='monologg/koelectra-base-discriminator', num_labels=8):
    dest_path = "models/koelectra_emotion.pt"
    os.makedirs("models", exist_ok=True)

    # Google Drive에서 다운로드
    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 Google Drive에서 모델 다운로드 중..."):
            gdown.download(url, dest_path, quiet=False)

    # 토크나이저 & 모델 로드
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = ElectraForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
    model.load_state_dict(torch.load(dest_path, map_location="cpu"))
    model.eval()

    return model, tokenizer
