# inference.py
import os
import torch
from typing import Tuple, Optional
import streamlit as st
from collections import Counter
from utils.load_model_from_drive import load_model_and_tokenizer_from_drive
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification
import soundfile as sf
import numpy as np
import librosa
import torch.nn as nn

# ─────────────────────────────────────────────────────────────────────────────
# 1) 모델 및 레이블 맵 설정
# ─────────────────────────────────────────────────────────────────────────────
MODEL_CONFIGS = [
    {"name":"koelectra","file_id":"1nCl-o_k9u2zcPT4sMcDsUlP1Y66VJaOw",
     "model_name":"monologg/koelectra-base-discriminator","type":"text",
     "label_map":{i:lbl for i,lbl in enumerate([
         "슬픔","소외","분노","불안","긍정","중립","당황","위협"
     ])}
    },
    {"name":"kcbert","file_id":"1i5xnpSkYu4gdKGgSU7VmMWOqyfYU626B",
     "model_name":"beomi/kcbert-base","type":"text",
     "label_map":{i:lbl for i,lbl in enumerate([
         "슬픔","소외","분노","불안","긍정","중립","당황","위협"
     ])}
    },
    {"name":"kluebert","file_id":"1ADvs5BQNsG757iWutSOdXyu3fN6e2Sgd",
     "model_name":"klue/bert-base","type":"text",
     "label_map":{i:lbl for i,lbl in enumerate([
         "슬픔","소외","분노","불안","긍정","중립","당황","위협"
     ])}
    },
    {"name":"hubert","file_id":"1v1k3_ZV0EYo4MhxbaeQM2gpKensokuuQ",
     "model_name":"facebook/hubert-base-ls960","type":"speech",
     # hubert logits index+1 → label_map
     "label_map":{1:"긍정",2:"슬픔",3:"분노",4:"불안",5:"소외",6:"당황",7:"중립"}
    },
    {"name":"cnn_speech","file_id":"18-zsM0w6ClOkovigkzTyfqgCwWGgA0ItID_5",
     "model_name":None,"type":"speech",
     # CNN 모델은 로컬 mel-spectrogram 기반 커스텀
     "label_map":{0:"슬픔",1:"소외",2:"분노",3:"불안",4:"긍정",5:"중립",6:"당황",7:"위협"}
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# CNNSpeech 정의 (mel-spectrogram 입력용)
# ─────────────────────────────────────────────────────────────────────────────
class CNNSpeech(nn.Module):
    def __init__(self, num_labels:int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32,64,3,padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64,128,3,padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.AdaptiveAvgPool2d((1,1))
        )
        self.fc = nn.Linear(128, num_labels)
    def forward(self,x):
        x = self.net(x)
        x = x.flatten(1)
        return self.fc(x)

# mel-spectrogram 계산 함수
def get_mel_spectrogram(path:str, sr:int=22050, n_mels:int=128, fmax:int=8000, width:int=128):
    y,_ = librosa.load(path, sr=sr)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, fmax=fmax)
    S_dB = librosa.power_to_db(S, ref=np.max)
    S_norm = (S_dB - S_dB.min())/(S_dB.max()-S_dB.min()+1e-6)
    if S_norm.shape[1] < width:
        S_norm = np.pad(S_norm, ((0,0),(0,width-S_norm.shape[1])), mode='constant')
    else:
        S_norm = S_norm[:,:width]
    return S_norm

# ─────────────────────────────────────────────────────────────────────────────
# 전역 캐시: 모델·토크나이저·프로세서 로드
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_ensemble():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    text_models, text_tokenizers = [], []
    speech_modalities = []

    for cfg in MODEL_CONFIGS:
        if cfg['type']=='text':
            # 1) 텍스트 모델·토크나이저 로드(Drive → 캐시)
            model, tokenizer = load_model_and_tokenizer_from_drive(
                file_id=cfg['file_id'],
                model_name=cfg['model_name'],
                num_labels=len(cfg['label_map'])
            )
            model.to(device).eval()
            text_models.append((model, cfg['label_map']))
            text_tokenizers.append(tokenizer)

        else:  # speech
            if cfg['name']=='hubert':
                # 2) 허버트는 FeatureExtractor
                feat_extractor = Wav2Vec2FeatureExtractor.from_pretrained(cfg['model_name'])
                mod = Wav2Vec2ForSequenceClassification.from_pretrained(
                    cfg['model_name'], num_labels=len(cfg['label_map'])
                )
                # fine-tuned weights 덮어씌우기
                wpath = os.path.join('models', f"{cfg['name']}_emotion.pt")
                if os.path.exists(wpath):
                    mod.load_state_dict(torch.load(wpath, map_location='cpu'), strict=False)
                mod.to(device).eval()
                speech_modalities.append((mod, feat_extractor, cfg['label_map'], cfg['name']))

            else:  # cnn_speech
                cnn = CNNSpeech(len(cfg['label_map']))
                wpath = os.path.join('models', f"{cfg['name']}_emotion.pt")
                if os.path.exists(wpath):
                    cnn.load_state_dict(torch.load(wpath, map_location='cpu'))
                cnn.to(device).eval()
                speech_modalities.append((cnn, None, cfg['label_map'], cfg['name']))

    return (text_models, text_tokenizers), speech_modalities


# ─────────────────────────────────────────────────────────────────────────────
# 예측: 하드 보팅 + 분기 처리
# ─────────────────────────────────────────────────────────────────────────────
def predict_emotion_with_score(
    text: Optional[str]=None,
    audio_path: Optional[str]=None
) -> Tuple[str,float]:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    votes = []
    # 텍스트 모델 예측
    if text:
        for (model,label_map),tokenizer in zip(text_models,text_tokenizers):
            inp = tokenizer(text,return_tensors='pt',padding=True,truncation=True,max_length=128).to(device)
            with torch.no_grad(): logits = model(**inp).logits
            idx = int(torch.argmax(logits,dim=-1).item())
            votes.append(label_map[idx])
    # 음성 모델 예측
    if audio_path:
        for model,proc,label_map,name in speech_modalities:
            if name=='hubert':
                audio, sr = sf.read(audio_path)
                # feature extractor 사용
                inputs = proc(audio, sampling_rate=sr, return_tensors='pt')
                input_values = inputs['input_values'].to(device)
                with torch.no_grad(): logits = model(input_values=input_values).logits
                idx = int(torch.argmax(logits,dim=-1).item())+1
                votes.append(label_map[idx])
            else:  # cnn
                S = get_mel_spectrogram(audio_path)
                x = torch.tensor(S,dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
                with torch.no_grad(): logits = model(x)
                idx = int(torch.argmax(logits,dim=-1).item())
                votes.append(label_map[idx])
    if not votes:
        raise ValueError('텍스트 또는 음성 입력을 제공해주세요.')
    vote,count = Counter(votes).most_common(1)[0]
    return vote, count/len(votes)
