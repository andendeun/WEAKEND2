import os
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 📁 경로 설정
FEEDBACK_PATH = "D:/workspace/Project/logs/gpt_feedback_log_cleaned.csv"
PDF_SAVE_DIR = "D:/workspace/Project/reports"
FONT_PATH = "D:/workspace/Project/fonts/NotoSansKR-Regular.ttf"
CHART_IMG_PATH = "D:/workspace/Project/temp/emotion_chart.png"

# 🔧 폰트 등록 (matplotlib + fpdf)
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = 'Noto Sans KR'

# 📊 차트 생성 함수
def generate_emotion_chart():
    df = pd.read_csv(FEEDBACK_PATH, quotechar='"')
    recent_df = df.tail(5)
    counts = recent_df['input_text'].value_counts()
    plt.figure(figsize=(6, 4))
    counts.plot(kind='bar', color='skyblue')
    plt.title("최근 감정 입력 빈도")
    plt.xlabel("문장")
    plt.ylabel("횟수")
    plt.tight_layout()
    plt.savefig(CHART_IMG_PATH)
    plt.close()

# ✅ PDF 클래스 정의
class PDF(FPDF):
    def header(self):
        self.set_font("Noto", 'B', 14)
        self.cell(0, 10, "감정 분석 피드백 리포트", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Noto", 'B', 12)
        self.cell(0, 10, title, ln=True, align="L")
        self.ln(2)

    def chapter_body(self, text):
        self.set_font("Noto", '', 11)
        self.multi_cell(0, 8, text)
        self.ln()

    def add_section(self, title, content):
        self.chapter_title(title)
        self.chapter_body(content)

# ✅ PDF 생성 실행 함수
def generate_pdf():
    os.makedirs(PDF_SAVE_DIR, exist_ok=True)
    df = pd.read_csv(FEEDBACK_PATH, quotechar='"')
    latest = df.tail(1).iloc[0]

    input_text = latest['input_text']
    full_feedback = latest['gpt_feedback']

    # 🔍 피드백 내용 분리
    if "[2]" in full_feedback:
        split_parts = full_feedback.split("[2]", 1)
        admin_review = split_parts[0].strip()
        user_feedback = split_parts[1].strip()
    else:
        admin_review = "(검토 내용 없음)"
        user_feedback = full_feedback.strip()

    timestamp = latest['timestamp'].replace(":", "-")
    filename_base = f"report_{timestamp}"

    # 📊 감정 흐름 차트 저장
    generate_emotion_chart()

    for target in ["user", "admin"]:
        pdf = PDF()
        pdf.add_font("Noto", "", FONT_PATH, uni=True)
        pdf.add_font("Noto", "B", FONT_PATH, uni=True)
        pdf.add_page()

        pdf.add_section("1. 입력 문장", input_text)
        pdf.add_section("2. 감정 피드백", user_feedback)

        if target == "admin":
            pdf.add_section("3. 감정 분석 리뷰 (Admin 전용)", admin_review)

        if os.path.exists(CHART_IMG_PATH):
            pdf.image(CHART_IMG_PATH, x=10, w=pdf.w - 20)

        save_path = os.path.join(PDF_SAVE_DIR, f"{filename_base}_{target}.pdf")
        pdf.output(save_path)

    print("✅ PDF 리포트 생성 완료!")
    print(f"📄 사용자용: {filename_base}_user.pdf")
    print(f"📄 관리자용: {filename_base}_admin.pdf")

if __name__ == "__main__":
    generate_pdf()
