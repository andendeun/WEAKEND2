import torch

# 정확한 .pt 파일 경로로 수정
state = torch.load(r"C:\eun\Workspaces\WEAKEND\models\kcbert_max.pt", map_location="cpu")

print(type(state))  # 이 결과가 'OrderedDict'인지 확인
