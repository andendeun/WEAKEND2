import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

# 공통 분류기 구조
class EmotionClassifier(nn.Module):
    def __init__(self, transformer, hidden_size, num_labels):
        super().__init__()
        self.transformer = transformer
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(hidden_size, num_labels)
    
    def forward(self, input_ids, attention_mask, **kwargs):
        output = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = output.last_hidden_state[:, 0]  # [CLS] 토큰 추출
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        probs = F.softmax(logits, dim=-1)
        return probs

# 수정된 앙상블 모델: 각 분류 레벨에 대해 별도의 분류기를 생성합니다.
class EnsembleEmotionModel:
    def __init__(self, num_labels_dict):
        """
        Args:
            num_labels_dict (dict): 각 분류 레벨마다의 라벨 개수를 담은 딕셔너리.
                                    예: {"대분류": 4, "중분류": 10, "소분류": 42}
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_labels_dict = num_labels_dict
        self.models = []
        
        # 사용할 모델 정보: (모델명, 사전학습 모델 경로)
        model_infos = [
            ("kcbert", "beomi/kcbert-base"),
            ("koelectra", "monologg/koelectra-base-discriminator"),
            ("klue", "klue/roberta-base")
        ]
        
        # 각 트랜스포머 모델에 대해, 각 분류 레벨별 분류기를 생성합니다.
        for model_name, model_path in model_infos:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            transformer_model = AutoModel.from_pretrained(model_path)
            classifiers = {}
            for level, num_labels in num_labels_dict.items():
                classifiers[level] = EmotionClassifier(transformer_model, 768, num_labels).to(self.device)
            self.models.append((model_name, tokenizer, classifiers))
        
        print("✅ 모델 로드 완료")
    
    def predict(self, text):
        """
        입력 텍스트에 대해 각 모델 및 각 레벨별 예측 확률을 계산합니다.
        반환 구조 예시:
        {
            "kcbert": {"대분류": tensor([...]), "중분류": tensor([...]), "소분류": tensor([...])},
            "koelectra": { ... },
            "klue": { ... }
        }
        """
        predictions = {}
        for model_name, tokenizer, classifiers in self.models:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            level_preds = {}
            with torch.no_grad():
                for level, classifier in classifiers.items():
                    probs = classifier(**inputs)
                    level_preds[level] = probs.squeeze(0)
            predictions[model_name] = level_preds
        return predictions

# 테스트 코드 (필요 시 개별 실행)
if __name__ == "__main__":
    label_counts = {"대분류": 4, "중분류": 10, "소분류": 42}
    model = EnsembleEmotionModel(num_labels_dict=label_counts)
    test_text = "나는 너를 사랑해"
    predictions = model.predict(test_text)
    for model_name, levels in predictions.items():
        print(f"\n[{model_name}]")
        for level, probs in levels.items():
            top_idx = probs.argmax().item()
            top_prob = probs[top_idx].item()
            print(f"  {level}: 인덱스 {top_idx} 확률 {top_prob:.2f}")
