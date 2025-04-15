import torch.nn as nn

class EmotionClassifier(nn.Module):
    def __init__(self, transformer, hidden_size=768, num_labels=3):
        super(EmotionClassifier, self).__init__()
        self.transformer = transformer
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, num_labels)
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0]
        return self.classifier(pooled_output)
