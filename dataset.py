import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

class EmotionDataset(Dataset):
    def __init__(self, csv_path, tokenizer=None, levels=["대분류", "중분류", "소분류"], max_length=128, model_name="kcbert"):
        """
        csv_path: CSV 파일 경로 (문자열) 또는 CSV 파일 경로들의 리스트.
        tokenizer: 사전 로딩된 토크나이저 객체. 없으면 model_name에 따라 내부 로드.
        levels: 자동 매핑할 열들 (예: ["대분류", "중분류", "소분류"])
        max_length: 토큰 최대 길이.
        model_name: 모델명 (예: "kcbert", "koelectra", "klue")
        """
        print("📂 CSV 로딩 시작...")
        # csv_path가 리스트인지 여부 확인 후 데이터프레임 결합
        if isinstance(csv_path, list):
            dfs = []
            for path in csv_path:
                try:
                    df_temp = pd.read_csv(path, encoding='utf-8')
                except UnicodeDecodeError:
                    df_temp = pd.read_csv(path, encoding='cp949')
                dfs.append(df_temp)
            self.df = pd.concat(dfs, ignore_index=True)
        elif isinstance(csv_path, str):
            try:
                self.df = pd.read_csv(csv_path, encoding='utf-8')
            except UnicodeDecodeError:
                self.df = pd.read_csv(csv_path, encoding='cp949')
        else:
            raise ValueError("csv_path는 문자열 또는 문자열 리스트여야 합니다.")

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

        # ✅ 토크나이저 설정 (외부에서 전달받지 않았다면 내부에서 AutoTokenizer 사용)
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
    csv_files = ["D:/workspace/Project_test/data/sample1.csv"]  # 테스트 경로

    dataset = EmotionDataset(
        csv_path=csv_files,
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
