import os
import torch
import gdown
import streamlit as st
from transformers import AutoTokenizer, AutoModel
from utils.emotion_classifier import EmotionClassifier

@st.cache_resource
def load_model_and_tokenizer_from_drive(file_id, model_name='monologg/koelectra-base-discriminator', num_labels=3):
    dest_path = "models/kcbert_max.pt"
    os.makedirs("models", exist_ok=True)

    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 모델 다운로드 중..."):
            gdown.download(url, dest_path, quiet=False)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    transformer = AutoModel.from_pretrained(model_name)

    model = EmotionClassifier(transformer, hidden_size=768, num_labels=num_labels)
    model.load_state_dict(torch.load(dest_path, map_location="cpu"))
    model.eval()

    return model, tokenizer
