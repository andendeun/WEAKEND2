import torch
from transformers import BertTokenizer, BertForSequenceClassification

def load_model(model_path):
    model = BertForSequenceClassification.from_pretrained("bert-base-multilingual-cased", num_labels=42)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model

def predict_emotion(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    predicted = torch.argmax(outputs.logits, dim=1)
    return predicted.item()
