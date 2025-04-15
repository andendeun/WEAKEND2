import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import ElectraTokenizer, ElectraForSequenceClassification
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import torch.nn.functional as F

import joblib  # 추가

plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows: 맑은 고딕
plt.rcParams['axes.unicode_minus'] = False     # 음수 마이너스 깨짐 방지

# 1. 데이터 로드pip i
df = pd.read_excel(r"C:\eun\Workspaces\FinalProject_Clean\sentence_test(1000).xlsx", sheet_name="data")
df = df[["문장", "중분류"]].dropna()

# 2. 라벨 인코딩
le = LabelEncoder()
df["label"] = le.fit_transform(df["중분류"])
num_labels = len(le.classes_)

# 3. Train/Test 분리
train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["문장"].tolist(), df["label"].tolist(), test_size=0.2, random_state=42
)

# 4. 토크나이저
tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-discriminator")

# 5. 커스텀 Dataset
class EmotionDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=max_len)
        self.labels = labels

    def __getitem__(self, idx):
        return {
            "input_ids": torch.tensor(self.encodings["input_ids"][idx]),
            "attention_mask": torch.tensor(self.encodings["attention_mask"][idx]),
            "labels": torch.tensor(self.labels[idx])
        }

    def __len__(self):
        return len(self.labels)

train_dataset = EmotionDataset(train_texts, train_labels, tokenizer)
test_dataset = EmotionDataset(test_texts, test_labels, tokenizer)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=16)

# 6. 모델 정의
model = ElectraForSequenceClassification.from_pretrained(
    "monologg/koelectra-base-discriminator", num_labels=num_labels
)
device = torch.device("cpu")
model.to(device)

optimizer = AdamW(model.parameters(), lr=2e-5)

# 7. 무한 학습 + 조기 종료 (85% 이상 시 저장 후 break)
epoch = 0
while True:
    epoch += 1
    model.train()
    total_loss = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch}"):
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    avg_loss = total_loss / len(train_loader)

    # 8. 평가
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            preds = torch.argmax(F.softmax(logits, dim=1), dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average="weighted")

    print(f"\n📘 Epoch {epoch}")
    print(f"🔹 Loss: {avg_loss:.4f}")
    print(f"✅ Accuracy: {acc:.4f}")
    print(f"✅ F1-score: {f1:.4f}")

    # 9. 조기 종료 조건
    if acc >= 0.95:
        print("🎉 목표 정확도 달성! 학습을 종료합니다.")
        torch.save(model.state_dict(), "koelectra_emotion.pt")
        print("📦 모델 저장 완료: koelectra_emotion.pt")
        break


# 라벨 인코딩
le = LabelEncoder()
df["label"] = le.fit_transform(df["중분류"])
num_labels = len(le.classes_)

# ✅ 저장 추가
joblib.dump(le, "label_encoder.pkl")
print("📦 라벨 인코더 저장 완료: label_encoder.pkl")


# Confusion Matrix
cm = confusion_matrix(all_labels, all_preds)
labels = le.classes_

plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap="Blues")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("confusion_matrix.png")  # 파일로 저장
plt.show()

# Classification Report
report = classification_report(all_labels, all_preds, target_names=labels)
print("\n📋 Classification Report:")
print(report)
