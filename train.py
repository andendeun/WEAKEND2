import os
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import AutoModel, AutoTokenizer

from dataset import EmotionDataset
from model import EmotionClassifier


def train_model(model_name, label_level, epochs=3, batch_size=16):
    print(f"\n🚀 학습 시작 - 모델명: {model_name}, 레벨: {label_level}, 에폭: {epochs}, 배치사이즈: {batch_size}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️  디바이스 설정: {'CUDA 사용(GPU)' if torch.cuda.is_available() else 'CPU 사용'}")

    # 1. 프리트레인 모델명 지정
    if model_name == "kcbert":
        pretrained = "beomi/kcbert-base"
    elif model_name == "koelectra":
        pretrained = "monologg/koelectra-base-discriminator"
    elif model_name == "klue":
        pretrained = "klue/roberta-base"
    else:
        raise ValueError(f"지원되지 않는 모델명입니다: {model_name}")

    # 2. 토크나이저 및 모델 로딩
    tokenizer = AutoTokenizer.from_pretrained(pretrained)
    base_model = AutoModel.from_pretrained(pretrained)
    model = EmotionClassifier(base_model, hidden_size=768, num_labels=None).to(device)
    print("✅ 모델 및 토크나이저 로딩 완료")

    # 3. 데이터 로딩
    csv_path = "D:/workspace/Project_test/data/sample1.csv"
    dataset = EmotionDataset(csv_path, levels=[label_level], model_name=model_name, tokenizer=tokenizer)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    print(f"📂 데이터 로드 완료: {len(dataset)}개 샘플")

    # 4. 레이블 수 추출 및 classifier 연결
    num_labels = len(dataset.label_mappings[label_level])
    model.classifier = torch.nn.Linear(768, num_labels).to(device)
    print(f"🎯 클래스 수 ({label_level}): {num_labels}")

    # 5. 옵티마이저
    optimizer = AdamW(model.parameters(), lr=2e-5)

    # 6. 학습 루프
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        print(f"\n📘 Epoch {epoch+1}/{epochs}")
        for batch_idx, batch in enumerate(dataloader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"][label_level].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = torch.nn.CrossEntropyLoss()(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            if (batch_idx + 1) % 10 == 0 or batch_idx == 0:
                print(f"  🔄 Step {batch_idx+1}/{len(dataloader)} | Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(dataloader)
        print(f"📊 Epoch {epoch+1} 완료 | 평균 Loss: {avg_loss:.4f}")

    # 7. 모델 저장
    save_dir = f"./checkpoints/{model_name}_{label_level}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "model.pt")
    torch.save(model.state_dict(), save_path)
    print(f"💾 모델 저장 완료: {save_path}")
    print("🎉 학습 완료!\n")


# ✅ 전체 모델-레벨 학습 루프 실행
if __name__ == "__main__":
    models = ["kcbert", "koelectra", "klue"]
    levels = ["대분류", "중분류", "소분류"]

    total_jobs = len(models) * len(levels)
    current_job = 1

    print(f"🧠 전체 학습 조합 수: {total_jobs}개")

    for model_name in models:
        for label_level in levels:
            print(f"\n============================")
            print(f"▶️ [{current_job}/{total_jobs}] 모델: {model_name.upper()} | 레벨: {label_level}")
            print(f"============================")
            try:
                train_model(model_name, label_level, epochs=3, batch_size=16)
                print(f"✅ 학습 성공 → 모델: {model_name.upper()}, 레벨: {label_level}")
            except Exception as e:
                print(f"❌ 학습 실패 → 모델: {model_name.upper()}, 레벨: {label_level}")
                print(f"에러: {e}")
            current_job += 1

    print("\n🎉 전체 모델/레벨 학습 완료!")
