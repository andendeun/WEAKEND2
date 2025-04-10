import os
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib import font_manager
import requests

# 📁 Google Drive 기반 경로 설정
FONT_FILE_ID = "1zR1CubH3E3sEquwJ4qt9yDvTJf-w_79m"  # NotoSansKR-Regular.ttf
FONT_PATH = "fonts/NotoSansKR-Regular.ttf"
FEEDBACK_PATH = "logs/gpt_feedback_log_cleaned.csv"
PDF_SAVE_DIR = "reports"
CHART_IMG_PATH = "temp/emotion_chart.png"

# ✅ Google Drive 폰트 다운로드 함수
def download_font():
    if not os.path.exists(FONT_PATH):
        print("📥 사용자 폰트 다운로드 중...")
        os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
        url = f"https://drive.google.com/uc?export=download&id={FONT_FILE_ID}"
        response = requests.get(url, stream=True)
        with open(FONT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        print("✅ 폰트 다운로드 완료")
    else:
        print("✅ 사용자 폰트 이미 존재")

# 🔧 폰트 등록
def setup_font():
    if os.path.exists(FONT_PATH):
        font_manager.fontManager.addfont(FONT_PATH)
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()
        print("✅ matplotlib에 폰트 적용 완료")
    else:
        print("⚠️ 폰트 없음 - 기본 폰트 사용")

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
    os.makedirs(os.path.dirname(CHART_IMG_PATH), exist_ok=True)
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
    download_font()
    setup_font()

    os.makedirs(PDF_SAVE_DIR, exist_ok=True)
    df = pd.read_csv(FEEDBACK_PATH, quotechar='"')
    latest = df.tail(1).iloc[0]

    input_text = latest['input_text']
    full_feedback = latest['gpt_feedback']

    if "[2]" in full_feedback:
        split_parts = full_feedback.split("[2]", 1)
        admin_review = split_parts[0].strip()
        user_feedback = split_parts[1].strip()
    else:
        admin_review = "(검토 내용 없음)"
        user_feedback = full_feedback.strip()

    timestamp = latest['timestamp'].replace(":", "-")
    filename_base = f"report_{timestamp}"

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
