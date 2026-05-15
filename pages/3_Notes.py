import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data import (
    load_notes,
    add_note,
    update_note,
    delete_note,
    get_all_note_tags,
    search_notes,
    get_user,
    get_users,
)
from utils.ui import inject_css, setup_sidebar

st.set_page_config(page_title="Notes - Family Hub", page_icon="📓", layout="wide")

current_user = setup_sidebar()
inject_css()

st.title("📓 Notes")

users = get_users()
user_id_to_name = {u["id"]: u["name"] for u in users}

# ── Tag filter in sidebar ──────────────────────────────────────────────────────
all_tags = get_all_note_tags()
with st.sidebar:
    tag_filter = st.multiselect("Filter by tags", all_tags, default=[])

# ── Session state ──────────────────────────────────────────────────────────────
if "show_add_note" not in st.session_state:
    st.session_state.show_add_note = False

# ── Top bar: search + New Note button ─────────────────────────────────────────
top1, top2 = st.columns([5, 1])
with top1:
    search_query = st.text_input("🔍 Search notes", placeholder="Search by title, content, or tag...")
with top2:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    if st.button("➕ New Note", use_container_width=True):
        st.session_state.show_add_note = True

# ── Add Note form ──────────────────────────────────────────────────────────────
if st.session_state.show_add_note:
    with st.container(border=True):
        st.subheader("New Note")
        new_title = st.text_input("Title", key="new_note_title")
        new_content = st.text_area(
            "Content",
            height=300,
            placeholder="Supports **markdown**...",
            key="new_note_content",
        )
        new_tags_raw = st.text_input("Tags (comma-separated)", key="new_note_tags")

        save_col, cancel_col = st.columns([1, 1])
        with save_col:
            if st.button("💾 Save Note", key="save_new_note"):
                if not new_title.strip():
                    st.error("Title is required.")
                else:
                    tags = [t.strip() for t in new_tags_raw.split(",") if t.strip()]
                    add_note(
                        title=new_title.strip(),
                        content=new_content,
                        tags=tags,
                        author=current_user["id"],
                    )
                    st.success("Note saved!")
                    st.session_state.show_add_note = False
                    st.rerun()
        with cancel_col:
            if st.button("✖ Cancel", key="cancel_new_note"):
                st.session_state.show_add_note = False
                st.rerun()

# ── Load and filter notes ──────────────────────────────────────────────────────
notes = search_notes(search_query)

if tag_filter:
    notes = [n for n in notes if any(tag in n.get("tags", []) for tag in tag_filter)]

# ── Note list ──────────────────────────────────────────────────────────────────
if not notes:
    st.info("No notes found.")
else:
    for note in notes:
        note_id = note["id"]
        edit_key = f"notes_edit_{note_id}"
        confirm_delete_key = f"notes_confirm_delete_{note_id}"

        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        author_name = user_id_to_name.get(note.get("author", ""), note.get("author", ""))
        updated_at = note.get("updated_at", "")
        try:
            updated_dt = datetime.fromisoformat(updated_at)
            updated_display = updated_dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            updated_display = updated_at[:10] if updated_at else "Unknown"

        expander_label = f"{note['title']} — {author_name}"

        with st.expander(expander_label):
            # Tags
            tags = note.get("tags", [])
            if tags:
                tag_html = " ".join(
                    f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
                    f'font-size:11px;background:#DBEAFE;color:#1D4ED8;margin:2px;">{tag}</span>'
                    for tag in tags
                )
                st.markdown(tag_html, unsafe_allow_html=True)

            st.caption(f"Last updated: {updated_display}")

            if not st.session_state[edit_key]:
                # View mode
                st.markdown(note.get("content", ""), unsafe_allow_html=False)

                action_col1, action_col2 = st.columns([1, 1])
                with action_col1:
                    if st.button("✏️ Edit", key=f"edit_btn_{note_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                with action_col2:
                    if st.button("🗑️ Delete", key=f"del_btn_{note_id}"):
                        st.session_state[confirm_delete_key] = True
                    if st.session_state.get(confirm_delete_key, False):
                        if st.checkbox("Confirm delete", key=f"confirm_del_{note_id}"):
                            delete_note(note_id)
                            st.rerun()
            else:
                # Edit mode
                with st.form(f"edit_note_form_{note_id}"):
                    edit_title = st.text_input("Title", value=note["title"])
                    edit_content = st.text_area(
                        "Content",
                        value=note.get("content", ""),
                        height=300,
                        placeholder="Supports **markdown**...",
                    )
                    edit_tags_raw = st.text_input(
                        "Tags (comma-separated)",
                        value=", ".join(note.get("tags", [])),
                    )
                    save_edit, cancel_edit = st.columns([1, 1])
                    with save_edit:
                        if st.form_submit_button("💾 Save Changes"):
                            if not edit_title.strip():
                                st.error("Title is required.")
                            else:
                                new_tags = [t.strip() for t in edit_tags_raw.split(",") if t.strip()]
                                update_note(
                                    note_id,
                                    title=edit_title.strip(),
                                    content=edit_content,
                                    tags=new_tags,
                                )
                                st.session_state[edit_key] = False
                                st.success("Note updated!")
                                st.rerun()
                    with cancel_edit:
                        if st.form_submit_button("✖ Cancel"):
                            st.session_state[edit_key] = False
                            st.rerun()
