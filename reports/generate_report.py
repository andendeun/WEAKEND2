from reports.emotion_trend_plot import plot_emotion_trend
from jinja2 import Template
import datetime

REPORT_TEMPLATE_PATH = "reports/templates/report_template.html"

def generate_html_report(user_id):
    plot_emotion_trend(user_id)
    with open(REPORT_TEMPLATE_PATH, encoding='utf-8') as f:
        template = Template(f.read())
    rendered = template.render(user_id=user_id, date=datetime.date.today())
    with open(f"reports/{user_id}_report.html", "w", encoding='utf-8') as f:
        f.write(rendered)
    return f"reports/{user_id}_report.html"
