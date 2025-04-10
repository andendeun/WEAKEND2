import os
import requests
import torch
from torch.utils.data import DataLoader
from dataset import EmotionDataset
from model import EmotionClassifier
from transformers import AutoModel
from tqdm import tqdm
import pandas as pd

# ✅ 사용할 Google Drive 파일 목록
FILE_IDS = {
    "sample1.xlsx": "1_o7DRLRewzZfnRjKCexu-KNLfTFK8_gX",
    "감성대화말뭉치_0407.xlsx": "<ID_추가>"
    # 필요 시 계속 추가 가능
}

def download_xlsx_from_drive(file_id, destination_path):
    if not os.path.exists(destination_path):
        print(f"📥 {destination_path} 다운로드 중...")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 다운로드 완료")
    else:
        print(f"✅ {destination_path} 이미 존재")

# ✅ 학습 관련 설정
def train(xlsx_filename="sample1.xlsx", model_name="kcbert", label_level="대분류", num_epochs=3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model_name == "kcbert":
        pretrained = "beomi/kcbert-base"
    elif model_name == "koelectra":
        pretrained = "monologg/koelectra-base-discriminator"
    elif model_name == "klue":
        pretrained = "klue/roberta-base"
    else:
        raise ValueError("지원되지 않는 모델입니다.")

    if xlsx_filename not in FILE_IDS:
        raise ValueError(f"❌ 지원되지 않는 파일입니다: {xlsx_filename}")

    xlsx_path = f"data/{xlsx_filename}"
    download_xlsx_from_drive(FILE_IDS[xlsx_filename], xlsx_path)

    # ✅ 데이터 로딩 및 임시 csv 저장
    df = pd.read_excel(xlsx_path, engine="openpyxl")
    temp_path = f"data/_temp_{os.path.splitext(xlsx_filename)[0]}.csv"
    df.to_csv(temp_path, index=False, encoding="utf-8-sig")

    dataset = EmotionDataset(temp_path, levels=[label_level], model_name=model_name)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

    base_model = AutoModel.from_pretrained(pretrained)
    model = EmotionClassifier(base_model, hidden_size=768, num_labels=len(dataset.label_mappings[label_level]))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    model.train()

    for epoch in range(num_epochs):
        total_loss = 0
        for batch in tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"][label_level].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss_fn = torch.nn.CrossEntropyLoss()
            loss = loss_fn(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"\n📉 Epoch {epoch+1}: 평균 Loss = {total_loss / len(dataloader):.4f}\n")

    # 모델 저장
    save_path = f"checkpoints/{model_name}_{label_level}/model.pt"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"✅ 모델 저장 완료: {save_path}")

# ✅ 단독 실행 시
if __name__ == "__main__":
    train(xlsx_filename="sample1.xlsx", model_name="kcbert", label_level="대분류", num_epochs=1)