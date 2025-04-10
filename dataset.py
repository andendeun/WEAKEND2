import os
import requests
import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

# ✅ Google Drive에서 sample1.xlsx 다운로드
XLSX_FILE_ID = "1_o7DRLRewzZfnRjKCexu-KNLfTFK8_gX"
xlsx_path = "data/sample1.xlsx"

def download_xlsx_from_drive(file_id, destination_path):
    if not os.path.exists(destination_path):
        print(f"📥 sample1.xlsx 다운로드 중: {destination_path}")
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 다운로드 완료")
    else:
        print("✅ sample1.xlsx 이미 존재")

# ✅ 다운로드 실행
download_xlsx_from_drive(XLSX_FILE_ID, xlsx_path)

class EmotionDataset(Dataset):
    def __init__(self, file_path, tokenizer=None, levels=["대분류", "중분류", "소분류"], max_length=128, model_name="kcbert"):
        """
        file_path: .xlsx 파일 경로 (문자열) 또는 .xlsx 경로 리스트
        tokenizer: 사전 로딩된 토크나이저 객체. 없으면 model_name에 따라 내부 로드.
        levels: 자동 매핑할 열들 (예: ["대분류", "중분류", "소분류"])
        max_length: 토큰 최대 길이
        model_name: 모델명 (예: "kcbert", "koelectra", "klue")
        """
        print("📂 XLSX 로딩 시작...")
        if isinstance(file_path, list):
            dfs = [pd.read_excel(path, engine='openpyxl') for path in file_path]
            self.df = pd.concat(dfs, ignore_index=True)
        elif isinstance(file_path, str):
            self.df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError("file_path는 문자열 또는 문자열 리스트여야 합니다.")

        self.df = self.df.dropna(subset=["문장"])
        self.levels = levels
        self.max_length = max_length

        print("🔧 감정 레벨 인덱스 매핑 중...")
        self.label_mappings = {}
        for level in levels:
            labels = self.df[level].fillna("NULL").tolist()
            unique_labels = sorted(set(labels))
            self.label_mappings[level] = {label: idx for idx, label in enumerate(unique_labels)}

        for level in levels:
            mapping = self.label_mappings[level]
            self.df[f"{level}_id"] = self.df[level].fillna("NULL").map(mapping)

        self.texts = self.df["문장"].tolist()

        if tokenizer is not None:
            self.tokenizer = tokenizer
            print("✅ 외부에서 전달받은 토크나이저 사용")
        else:
            print(f"🔍 모델명 기반 토크나이저 로딩: {model_name}")
            if model_name == "kcbert":
                pretrained = "beomi/kcbert-base"
            elif model_name == "koelectra":
                pretrained = "monologg/koelectra-base-discriminator"
            elif model_name == "klue":
                pretrained = "klue/roberta-base"
            else:
                raise ValueError(f"지원되지 않는 모델명입니다: {model_name}")

            self.tokenizer = AutoTokenizer.from_pretrained(pretrained)
            print(f"✅ {model_name} 토크나이저 로딩 완료")

        print("✏️ 문장 토큰화 시작...")
        self.encodings = self.tokenizer(
            self.texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        print(f"✅ 토큰화 완료: 총 {len(self.texts)}개 문장\n")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        labels = {
            level: torch.tensor(self.df.iloc[idx][f"{level}_id"])
            for level in self.levels
        }
        item["labels"] = labels
        return item

# ✅ 테스트 코드 (단독 실행 시)
if __name__ == "__main__":
    print("🧪 EmotionDataset 단독 테스트 실행 중...\n")
    dataset = EmotionDataset(
        file_path=xlsx_path,
        levels=["대분류", "중분류", "소분류"],
        model_name="kcbert"
    )

    print("📊 레이블 매핑 결과:")
    for level, mapping in dataset.label_mappings.items():
        print(f"  {level}: {mapping}")

    print(f"\n📦 샘플 개수: {len(dataset)}")
    print("🔍 첫 번째 샘플 확인:")
    sample = dataset[0]
    print("input_ids[:10]:", sample["input_ids"][:10])
    print("attention_mask[:10]:", sample["attention_mask"][:10])
    print("labels:", {k: v.item() for k, v in sample["labels"].items()})
