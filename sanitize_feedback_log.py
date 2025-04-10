import pandas as pd
import csv

# 원본 파일 경로
INPUT_PATH = "D:/workspace/Project/logs/gpt_feedback_log.csv"
# 정제된 파일 저장 경로
OUTPUT_PATH = "D:/workspace/Project/logs/gpt_feedback_log_cleaned.csv"

# 기대하는 열 수 (timestamp, input_text, gpt_feedback)
EXPECTED_COLS = 3

def sanitize_csv(input_path, output_path, expected_cols=3):
    clean_rows = []
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, quotechar='"', escapechar='\\')
        for i, row in enumerate(reader, start=1):
            if len(row) == expected_cols:
                clean_rows.append(row)
            else:
                print(f"⚠️ Skipping malformed line {i}: {row}")

    with open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out, quotechar='"', escapechar='\\', quoting=csv.QUOTE_ALL)
        writer.writerows(clean_rows)

    print(f"✅ 정제 완료! 👉 {output_path}")
    print(f"🧾 정제된 총 줄 수: {len(clean_rows)}")

if __name__ == "__main__":
    sanitize_csv(INPUT_PATH, OUTPUT_PATH, EXPECTED_COLS)
