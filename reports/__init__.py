# reports/__init__.py
"""
Package for report utilities.
"""
# 기본 리포트 기능만 노출
from .generate_report import get_emotion_report
from .generate_report import create_pdf_report

# emotion_trend_plot 모듈은 필요 시 명시적으로 import
#__all__ = ['get_emotion_report', 'create_pdf_report']
