import sys
from pathlib import Path
from datetime import date, datetime, timedelta

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from utils.data import (
    load_tasks,
    PRIORITY_EMOJI,
)
from utils.ui import inject_css, setup_sidebar

st.set_page_config(page_title="Family Hub", page_icon="🏠", layout="wide")

current_user = setup_sidebar()
inject_css()

today = date.today()
today_str = today.strftime("%Y-%m-%d")

hour = datetime.now().hour
if hour < 12:
    greeting = "Good morning"
elif hour < 17:
    greeting = "Good afternoon"
else:
    greeting = "Good evening"

st.title(f"🏠 {greeting}, {current_user['name']}!")
st.caption(today.strftime("%A, %B %d, %Y"))

tasks = load_tasks()

# Metrics
week_end = (today + timedelta(days=7)).strftime("%Y-%m-%d")

overdue = [
    t for t in tasks
    if t.get("due_date") and t["due_date"] < today_str and t["status"] != "Done"
]
due_today = [
    t for t in tasks
    if t.get("due_date") == today_str and t["status"] != "Done"
]
this_week = [
    t for t in tasks
    if t.get("due_date") and today_str < t["due_date"] <= week_end and t["status"] != "Done"
]
done_today = [
    t for t in tasks
    if t.get("updated_at", "")[:10] == today_str and t["status"] == "Done"
]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🔴 Overdue", len(overdue))
with col2:
    st.metric("📅 Due Today", len(due_today))
with col3:
    st.metric("📆 This Week", len(this_week))
with col4:
    st.metric("✅ Done Today", len(done_today))

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("📋 Today's Tasks")
    todays_tasks = sorted(
        overdue + due_today,
        key=lambda t: (t.get("due_date") or "", t.get("priority", ""))
    )
    if not todays_tasks:
        st.info("No tasks due today. Enjoy your day! 🎉")
    else:
        for task in todays_tasks:
            priority_emoji = PRIORITY_EMOJI.get(task.get("priority", "Medium"), "")
            labels = task.get("labels", [])
            label_str = " ".join(
                f'<span class="label-chip">{lbl}</span>' for lbl in labels
            )
            overdue_badge = ""
            if task.get("due_date") and task["due_date"] < today_str:
                overdue_badge = ' <span style="color:#EF4444;font-size:11px;">OVERDUE</span>'
            st.markdown(
                f"""<div class="task-card">
                  <strong>{priority_emoji} {task['title']}</strong>{overdue_badge}<br>
                  <small>{label_str}</small>
                </div>""",
                unsafe_allow_html=True,
            )

with right_col:
    st.subheader("🔮 Coming Up")
    upcoming = sorted(this_week, key=lambda t: t.get("due_date", ""))
    if not upcoming:
        st.info("Nothing due in the next 7 days.")
    else:
        for task in upcoming:
            due = date.fromisoformat(task["due_date"])
            days_away = (due - today).days
            day_label = f"in {days_away} day{'s' if days_away != 1 else ''}"
            priority_emoji = PRIORITY_EMOJI.get(task.get("priority", "Medium"), "")
            st.markdown(
                f"""<div class="task-card">
                  <strong>{priority_emoji} {task['title']}</strong><br>
                  <small style="color:#6B7280;">{due.strftime('%b %d')} — {day_label}</small>
                </div>""",
                unsafe_allow_html=True,
            )

st.divider()
st.markdown(
    "<div style='text-align:center;color:#9CA3AF;font-size:13px;'>Family Hub — built with Streamlit</div>",
    unsafe_allow_html=True,
)
