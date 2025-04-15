import os
import torch
from torch.utils.data import DataLoader, random_split
from dataset import EmotionDataset
from model import EmotionClassifier
from transformers import AutoModel
from tqdm import tqdm
from sklearn.metrics import accuracy_score

def compute_accuracy(preds, labels):
    pred_ids = torch.argmax(preds, dim=1).cpu().numpy()
    label_ids = labels.cpu().numpy()
    return accuracy_score(label_ids, pred_ids)

def train(xlsx_path, model_name="kcbert", label_level="대분류", num_epochs=3, batch_size=16):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model_name == "kcbert":
        pretrained = "beomi/kcbert-base"
    elif model_name == "koelectra":
        pretrained = "monologg/koelectra-base-discriminator"
    elif model_name == "klue":
        pretrained = "klue/roberta-base"
    else:
        raise ValueError("지원되지 않는 모델입니다.")

    # 전체 데이터셋 로딩 → train/val 분할
    full_dataset = EmotionDataset(xlsx_path, levels=[label_level], model_name=model_name)
    total_len = len(full_dataset)
    train_len = int(0.8 * total_len)
    val_len = total_len - train_len
    train_dataset, val_dataset = random_split(full_dataset, [train_len, val_len])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    base_model = AutoModel.from_pretrained(pretrained)
    model = EmotionClassifier(base_model, hidden_size=768, num_labels=len(full_dataset.label_mappings[label_level]))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    loss_fn = torch.nn.CrossEntropyLoss()

    for epoch in range(num_epochs):
        # 학습
        model.train()
        train_loss = 0
        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Train]"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"][label_level].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # 검증
        model.eval()
        val_loss = 0
        all_preds, all_labels = [], []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"][label_level].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = loss_fn(outputs, labels)
                val_loss += loss.item()

                all_preds.append(outputs)
                all_labels.append(labels)

        all_preds = torch.cat(all_preds, dim=0)
        all_labels = torch.cat(all_labels, dim=0)
        val_acc = compute_accuracy(all_preds, all_labels)

        print(f"\n📊 Epoch {epoch+1}/{num_epochs} | Train Loss: {train_loss / len(train_loader):.4f} | "
              f"Val Loss: {val_loss / len(val_loader):.4f} | Val Acc: {val_acc:.4f}\n")

    # 모델 저장
    save_path = f"../checkpoints/{model_name}_{label_level}/model.pt"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"모델 저장 완료: {save_path}")

if __name__ == "__main__":
    xlsx_path = r"C:\eun\Workspaces\FinalProject_Clean\data\data_final_250410.xlsx"
    train(xlsx_path=xlsx_path, model_name="kcbert", label_level="대분류", num_epochs=1)
