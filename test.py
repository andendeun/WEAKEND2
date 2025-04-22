from streamlit_option_menu import option_menu

# 상단에 수평 메뉴
selected = option_menu(
    menu_title=None,
    options=["🏠 Home", "📊 Report", "🎯 Recommend"],
    default_index=0,
    orientation="horizontal",
)
# or 사이드바에
# with st.sidebar:
#     selected = option_menu(..., orientation="vertical")

if selected == "🏠 Home":
    "…홈 페이지 렌더링…"
elif selected == "📊 Report":
    "…리포트 렌더링…"
