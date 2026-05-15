import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data import get_users

COMMON_CSS = """
<style>
/* Clean card style */
.task-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    background: white;
}
.priority-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    color: white;
}
.label-chip {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 12px;
    font-size: 11px;
    background: #e5e7eb;
    color: #374151;
    margin: 1px;
}
.user-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 4px;
}
</style>
"""


def inject_css():
    st.markdown(COMMON_CSS, unsafe_allow_html=True)


def setup_sidebar():
    """Sets up sidebar with user selector. Returns current user dict."""
    if "current_user" not in st.session_state:
        st.session_state.current_user = "user1"

    users = get_users()

    with st.sidebar:
        st.markdown("# 🏠 Family Hub")
        st.divider()

        user_map = {u["name"]: u["id"] for u in users}
        current_name = next(
            (u["name"] for u in users if u["id"] == st.session_state.current_user),
            users[0]["name"],
        )

        selected_name = st.selectbox(
            "👤 Logged in as",
            list(user_map.keys()),
            index=list(user_map.keys()).index(current_name),
        )
        st.session_state.current_user = user_map[selected_name]

        st.divider()

    return next(u for u in users if u["id"] == st.session_state.current_user)
