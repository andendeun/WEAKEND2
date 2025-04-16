import json
from sklearn.preprocessing import LabelEncoder

# 예시: 클래스 목록
labels = [
    "행복/기쁨/감사",
    "신뢰/편안/존경/안정",
    "분노/짜증/불편",
    "당황/충격/배신감",
    "공포/불안",
    "고독/외로움/소외감/허탈",
    "죄책감/미안함",
    "걱정/고민/긴장"
]

# 인코딩 및 저장
le = LabelEncoder()
le.fit(labels)

# 저장 (class_to_index 형태)
with open("label_encoder.json", "w", encoding="utf-8") as f:
    json.dump({label: int(le.transform([label])[0]) for label in le.classes_}, f, ensure_ascii=False)
