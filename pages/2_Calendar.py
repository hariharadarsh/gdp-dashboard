import sys
import calendar
from pathlib import Path
from datetime import date, datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data import (
    load_tasks,
    get_users,
    PRIORITY_COLORS,
)
from utils.ui import inject_css, setup_sidebar

st.set_page_config(page_title="Calendar - Family Hub", page_icon="📅", layout="wide")

current_user = setup_sidebar()
inject_css()

st.title("📅 Calendar")

today = date.today()

# ── Session state for month navigation ────────────────────────────────────────
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month

# ── Month navigation ──────────────────────────────────────────────────────────
nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

with nav_col1:
    if st.button("◀ Prev", use_container_width=True):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with nav_col2:
    month_name = datetime(st.session_state.cal_year, st.session_state.cal_month, 1).strftime("%B %Y")
    st.markdown(
        f"<h2 style='text-align:center;margin:0;'>{month_name}</h2>",
        unsafe_allow_html=True,
    )

with nav_col3:
    if st.button("Next ▶", use_container_width=True):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

# ── Filters ────────────────────────────────────────────────────────────────────
users = get_users()
f1, f2 = st.columns([3, 1])
with f1:
    show_user_names = st.multiselect(
        "Show users",
        [u["name"] for u in users],
        default=[u["name"] for u in users],
    )
with f2:
    show_done = st.checkbox("Show completed tasks", value=False)

user_name_to_id = {u["name"]: u["id"] for u in users}
show_user_ids = [user_name_to_id[n] for n in show_user_names]

# ── Load and filter tasks ──────────────────────────────────────────────────────
all_tasks = load_tasks()

def task_passes_filters(task):
    if not show_done and task.get("status") == "Done":
        return False
    if show_user_ids:
        assigned = task.get("assigned_to", [])
        # Show task if unassigned or if any assigned user is in filter
        if assigned and not any(uid in show_user_ids for uid in assigned):
            return False
    return True

filtered_tasks = [t for t in all_tasks if task_passes_filters(t)]


# ── Calendar HTML generator ────────────────────────────────────────────────────
def generate_calendar_html(year, month, tasks, users):
    today_str = date.today().strftime("%Y-%m-%d")
    user_id_to_color = {u["id"]: u["color"] for u in users}

    # Build a dict: date_str -> list of tasks
    tasks_by_date = {}
    for task in tasks:
        dd = task.get("due_date")
        if dd:
            tasks_by_date.setdefault(dd, []).append(task)

    weeks = calendar.monthcalendar(year, month)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    html = """
<style>
.cal-table {
    width: 100%;
    border-collapse: collapse;
    font-family: sans-serif;
}
.cal-table th {
    background: #F3F4F6;
    text-align: center;
    padding: 8px;
    font-size: 13px;
    color: #374151;
    border: 1px solid #E5E7EB;
}
.cal-table td {
    vertical-align: top;
    border: 1px solid #E5E7EB;
    padding: 4px 6px;
    min-height: 90px;
    width: 14.28%;
    height: 90px;
}
.cal-table td:hover {
    background: #F9FAFB;
}
.cal-day-num {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
}
.cal-day-num.today {
    background: #3B82F6;
    color: white;
    border-radius: 50%;
    display: inline-block;
    width: 22px;
    height: 22px;
    text-align: center;
    line-height: 22px;
}
.cal-day-num.past {
    color: #9CA3AF;
}
.cal-task-chip {
    display: block;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 11px;
    color: white;
    margin: 1px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}
.cal-more {
    font-size: 10px;
    color: #6B7280;
    margin-top: 2px;
}
.cal-empty {
    background: #FAFAFA;
}
</style>
<table class="cal-table">
<thead><tr>
"""
    for dn in day_names:
        html += f"<th>{dn}</th>"
    html += "</tr></thead><tbody>"

    for week in weeks:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += '<td class="cal-empty"></td>'
            else:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                is_today = date_str == today_str
                is_past = date_str < today_str

                day_class = "today" if is_today else ("past" if is_past else "")
                html += "<td>"
                html += f'<div class="cal-day-num {day_class}">{day}</div>'

                day_tasks = tasks_by_date.get(date_str, [])
                shown = day_tasks[:3]
                extra = len(day_tasks) - 3

                for task in shown:
                    priority = task.get("priority", "Medium")
                    color = PRIORITY_COLORS.get(priority, "#9CA3AF")
                    title = task.get("title", "")
                    if len(title) > 18:
                        title = title[:18] + "..."
                    html += f'<span class="cal-task-chip" style="background:{color};" title="{task.get("title", "")}">{title}</span>'

                if extra > 0:
                    html += f'<div class="cal-more">+{extra} more</div>'

                html += "</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html


# ── Render calendar ────────────────────────────────────────────────────────────
cal_html = generate_calendar_html(
    st.session_state.cal_year,
    st.session_state.cal_month,
    filtered_tasks,
    users,
)
st.markdown(cal_html, unsafe_allow_html=True)

st.divider()

# ── Selected date detail ───────────────────────────────────────────────────────
st.subheader("Tasks for a specific date")
selected_date = st.date_input("View tasks for date:", value=today)
selected_str = selected_date.strftime("%Y-%m-%d")

date_tasks = [t for t in filtered_tasks if t.get("due_date") == selected_str]

if not date_tasks:
    st.info("No tasks on this date.")
else:
    user_id_to_name = {u["id"]: u["name"] for u in users}
    user_id_to_color = {u["id"]: u["color"] for u in users}
    from utils.data import PRIORITY_EMOJI, STATUS_EMOJI
    for task in date_tasks:
        priority_emoji = PRIORITY_EMOJI.get(task.get("priority", "Medium"), "")
        status_emoji = STATUS_EMOJI.get(task.get("status", "To Do"), "")
        labels = task.get("labels", [])
        label_str = " ".join(f'<span class="label-chip">{lbl}</span>' for lbl in labels)
        assigned_parts = []
        for uid in task.get("assigned_to", []):
            color = user_id_to_color.get(uid, "#9CA3AF")
            name = user_id_to_name.get(uid, uid)
            assigned_parts.append(
                f'<span class="user-dot" style="background:{color};display:inline-block;'
                f'width:10px;height:10px;border-radius:50%;margin-right:4px;"></span>'
                f'<span style="font-size:12px;">{name}</span>'
            )
        assigned_str = " ".join(assigned_parts)
        st.markdown(
            f"""<div class="task-card">
              <strong>{status_emoji} {priority_emoji} {task['title']}</strong><br>
              <small>{label_str} {assigned_str}</small>
            </div>""",
            unsafe_allow_html=True,
        )
