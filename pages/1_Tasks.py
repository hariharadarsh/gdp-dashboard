import sys
from pathlib import Path
from datetime import date, datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data import (
    load_tasks,
    add_task,
    update_task,
    delete_task,
    get_all_labels,
    get_users,
    get_user,
    PRIORITY_COLORS,
    PRIORITY_EMOJI,
    STATUS_EMOJI,
)
from utils.ui import inject_css, setup_sidebar

st.set_page_config(page_title="Tasks - Family Hub", page_icon="📝", layout="wide")

current_user = setup_sidebar()
inject_css()

st.title("📝 Tasks")

users = get_users()
user_name_to_id = {u["name"]: u["id"] for u in users}
user_id_to_name = {u["id"]: u["name"] for u in users}
user_id_to_color = {u["id"]: u["color"] for u in users}

# ── Add Task form ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Task", expanded=False):
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Title *")
        description = st.text_area("Description")
        col_a, col_b = st.columns(2)
        with col_a:
            use_due_date = st.checkbox("Set due date", value=False)
            due_date_val = st.date_input("Due Date", value=date.today()) if use_due_date else None
        with col_b:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
        labels_raw = st.text_input("Labels (comma-separated)")
        assigned_names = st.multiselect(
            "Assign to",
            [u["name"] for u in users],
        )
        submitted = st.form_submit_button("Add Task")
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                labels = [l.strip() for l in labels_raw.split(",") if l.strip()]
                assigned_ids = [user_name_to_id[n] for n in assigned_names]
                add_task(
                    title=title.strip(),
                    description=description,
                    due_date=due_date_val,
                    priority=priority,
                    labels=labels,
                    assigned_to=assigned_ids,
                )
                st.success(f"Task '{title}' added!")
                st.rerun()

# ── Filters ────────────────────────────────────────────────────────────────────
all_labels = get_all_labels()
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
with fc1:
    priority_filter = st.multiselect(
        "Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"]
    )
with fc2:
    user_filter_names = st.multiselect(
        "Assigned to", [u["name"] for u in users], default=[]
    )
with fc3:
    label_filter = st.multiselect("Labels", all_labels, default=[])
with fc4:
    search_text = st.text_input("Search", placeholder="Search tasks...")

tasks = load_tasks()
today_str = date.today().strftime("%Y-%m-%d")


def passes_filters(task):
    if task.get("priority") not in priority_filter:
        return False
    if user_filter_names:
        assigned_names_task = [user_id_to_name.get(uid, "") for uid in task.get("assigned_to", [])]
        if not any(n in assigned_names_task for n in user_filter_names):
            return False
    if label_filter:
        if not any(lbl in task.get("labels", []) for lbl in label_filter):
            return False
    if search_text:
        q = search_text.lower()
        if q not in task.get("title", "").lower() and q not in task.get("description", "").lower():
            return False
    return True


def render_task(task):
    task_id = task["id"]
    edit_key = f"tasks_edit_{task_id}"
    confirm_delete_key = f"tasks_confirm_delete_{task_id}"

    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    with st.container(border=True):
        # Row 1: status toggle, priority emoji, title
        r1c1, r1c2 = st.columns([1, 11])
        with r1c1:
            status_cycle = {"To Do": "In Progress", "In Progress": "Done", "Done": "To Do"}
            next_status = status_cycle[task["status"]]
            if st.button(STATUS_EMOJI.get(task["status"], "⬜"), key=f"status_{task_id}",
                         help=f"Click to set: {next_status}"):
                update_task(task_id, status=next_status)
                st.rerun()
        with r1c2:
            p_emoji = PRIORITY_EMOJI.get(task.get("priority", "Medium"), "")
            st.markdown(f"**{p_emoji} {task['title']}**")

        # Row 2: due date, labels, assigned users
        meta_parts = []
        if task.get("due_date"):
            due_str = task["due_date"]
            color = "#EF4444" if due_str < today_str else "#6B7280"
            meta_parts.append(
                f'<span style="color:{color};font-size:12px;">📅 {due_str}</span>'
            )
        for lbl in task.get("labels", []):
            meta_parts.append(f'<span class="label-chip">{lbl}</span>')
        for uid in task.get("assigned_to", []):
            ucolor = user_id_to_color.get(uid, "#9CA3AF")
            uname = user_id_to_name.get(uid, uid)
            meta_parts.append(
                f'<span><span class="user-dot" style="background:{ucolor};"></span>'
                f'<span style="font-size:12px;">{uname}</span></span>'
            )
        if meta_parts:
            st.markdown(" &nbsp; ".join(meta_parts), unsafe_allow_html=True)

        # Row 3: Edit expander + Delete
        ec1, ec2 = st.columns([6, 1])
        with ec1:
            with st.expander("✏️ Edit"):
                with st.form(f"edit_form_{task_id}"):
                    new_title = st.text_input("Title", value=task["title"])
                    new_desc = st.text_area("Description", value=task.get("description", ""))
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        has_due = task.get("due_date") is not None
                        use_due = st.checkbox("Set due date", value=has_due, key=f"use_due_{task_id}")
                        if use_due:
                            default_due = date.fromisoformat(task["due_date"]) if task.get("due_date") else date.today()
                            new_due = st.date_input("Due Date", value=default_due, key=f"due_{task_id}")
                        else:
                            new_due = None
                    with ecol2:
                        priorities = ["High", "Medium", "Low"]
                        new_priority = st.selectbox(
                            "Priority", priorities,
                            index=priorities.index(task.get("priority", "Medium")),
                            key=f"priority_{task_id}",
                        )
                        statuses = ["To Do", "In Progress", "Done"]
                        new_status = st.selectbox(
                            "Status", statuses,
                            index=statuses.index(task.get("status", "To Do")),
                            key=f"status_select_{task_id}",
                        )
                    new_labels_raw = st.text_input(
                        "Labels (comma-separated)",
                        value=", ".join(task.get("labels", [])),
                        key=f"labels_{task_id}",
                    )
                    current_assigned_names = [
                        user_id_to_name[uid]
                        for uid in task.get("assigned_to", [])
                        if uid in user_id_to_name
                    ]
                    new_assigned_names = st.multiselect(
                        "Assign to",
                        [u["name"] for u in users],
                        default=current_assigned_names,
                        key=f"assigned_{task_id}",
                    )
                    save_btn = st.form_submit_button("Save Changes")
                    if save_btn:
                        new_labels = [l.strip() for l in new_labels_raw.split(",") if l.strip()]
                        new_assigned_ids = [user_name_to_id[n] for n in new_assigned_names]
                        update_task(
                            task_id,
                            title=new_title,
                            description=new_desc,
                            due_date=new_due,
                            priority=new_priority,
                            status=new_status,
                            labels=new_labels,
                            assigned_to=new_assigned_ids,
                        )
                        st.success("Task updated!")
                        st.rerun()
        with ec2:
            if st.button("🗑️", key=f"del_btn_{task_id}", help="Delete task"):
                st.session_state[confirm_delete_key] = True
            if st.session_state.get(confirm_delete_key, False):
                if st.checkbox("Confirm delete", key=f"confirm_del_{task_id}"):
                    delete_task(task_id)
                    st.rerun()


# ── Task Tabs ──────────────────────────────────────────────────────────────────
tab_todo, tab_inprogress, tab_done = st.tabs(["⬜ To Do", "🔄 In Progress", "✅ Done"])

for tab, status in [
    (tab_todo, "To Do"),
    (tab_inprogress, "In Progress"),
    (tab_done, "Done"),
]:
    with tab:
        filtered = [t for t in tasks if t["status"] == status and passes_filters(t)]
        # Sort: overdue first, then by due date, then by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        filtered.sort(key=lambda t: (
            t.get("due_date") or "9999-99-99",
            priority_order.get(t.get("priority", "Medium"), 1),
        ))
        if not filtered:
            st.info("No tasks here.")
        else:
            for task in filtered:
                render_task(task)
