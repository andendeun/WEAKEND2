import os
import torch
import gdown
import streamlit as st
from transformers import BertTokenizer, BertForSequenceClassification

@st.cache_resource
def load_model_and_tokenizer_from_drive(file_id, num_labels=42):
    dest_path = "models/kcbert_max.pt"
    os.makedirs("models", exist_ok=True)

    # Google Drive에서 다운로드
    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 모델 다운로드 중..."):
            gdown.download(url, dest_path, quiet=False)

    # 모델 로드
    model = BertForSequenceClassification.from_pretrained("monologg/kobert", num_labels=num_labels)
    model.load_state_dict(torch.load(dest_path, map_location=torch.device("cpu")))
    model.eval()

    # 토크나이저 로드
    tokenizer = BertTokenizer.from_pretrained("monologg/kobert")

    return model, tokenizer
