import os
import torch
import gdown
import streamlit as st
from transformers import ElectraTokenizer, ElectraForSequenceClassification

@st.cache_resource
def load_model_and_tokenizer_from_drive(file_id):
    dest_path = "models/koelectra_emotion.pt"
    os.makedirs("models", exist_ok=True)

    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 모델 다운로드 중..."):
            gdown.download(url, dest_path, quiet=False)

    tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-discriminator")
    model = ElectraForSequenceClassification.from_pretrained(
        "monologg/koelectra-base-discriminator", num_labels=8  # 중분류 기준
    )
    model.load_state_dict(torch.load(dest_path, map_location="cpu"))
    model.eval()

    return model, tokenizer
