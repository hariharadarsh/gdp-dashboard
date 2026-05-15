import json
import uuid
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
NOTES_FILE = DATA_DIR / "notes.json"
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "users": [
        {"id": "user1", "name": "Me", "color": "#3B82F6"},
        {"id": "user2", "name": "Wife", "color": "#EC4899"},
    ]
}

PRIORITY_COLORS = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}
PRIORITY_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
STATUS_EMOJI = {"To Do": "⬜", "In Progress": "🔄", "Done": "✅"}


def _ensure_data():
    DATA_DIR.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]")
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]")


def load_config():
    _ensure_data()
    return json.loads(CONFIG_FILE.read_text())


def save_config(config):
    _ensure_data()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_users():
    return load_config().get("users", [])


def get_user(user_id):
    for u in get_users():
        if u["id"] == user_id:
            return u
    return None


def load_tasks():
    _ensure_data()
    return json.loads(TASKS_FILE.read_text())


def save_tasks(tasks):
    _ensure_data()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def add_task(title, description="", due_date=None, priority="Medium",
             labels=None, assigned_to=None, status="To Do"):
    tasks = load_tasks()
    now = datetime.now().isoformat()
    due_str = None
    if due_date is not None:
        if isinstance(due_date, date):
            due_str = due_date.strftime("%Y-%m-%d")
        else:
            due_str = str(due_date)
    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "due_date": due_str,
        "priority": priority,
        "labels": labels or [],
        "assigned_to": assigned_to or [],
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    tasks.append(task)
    save_tasks(tasks)
    return task


def update_task(task_id, **updates):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            for k, v in updates.items():
                if k == "due_date" and isinstance(v, date):
                    v = v.strftime("%Y-%m-%d")
                task[k] = v
            task["updated_at"] = datetime.now().isoformat()
            break
    save_tasks(tasks)


def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)


def get_all_labels():
    tasks = load_tasks()
    labels = set()
    for t in tasks:
        for lbl in t.get("labels", []):
            if lbl.strip():
                labels.add(lbl.strip())
    return sorted(labels)


def load_notes():
    _ensure_data()
    return json.loads(NOTES_FILE.read_text())


def save_notes(notes):
    _ensure_data()
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def add_note(title, content, tags=None, author=None):
    notes = load_notes()
    now = datetime.now().isoformat()
    note = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "tags": tags or [],
        "author": author or "user1",
        "created_at": now,
        "updated_at": now,
    }
    notes.append(note)
    save_notes(notes)
    return note


def update_note(note_id, **updates):
    notes = load_notes()
    for note in notes:
        if note["id"] == note_id:
            for k, v in updates.items():
                note[k] = v
            note["updated_at"] = datetime.now().isoformat()
            break
    save_notes(notes)


def delete_note(note_id):
    notes = load_notes()
    notes = [n for n in notes if n["id"] != note_id]
    save_notes(notes)


def get_all_note_tags():
    notes = load_notes()
    tags = set()
    for n in notes:
        for tag in n.get("tags", []):
            if tag.strip():
                tags.add(tag.strip())
    return sorted(tags)


def search_notes(query):
    notes = load_notes()
    if not query:
        return sorted(notes, key=lambda n: n.get("updated_at", ""), reverse=True)
    q = query.lower()
    results = []
    for n in notes:
        if (q in n.get("title", "").lower()
                or q in n.get("content", "").lower()
                or any(q in tag.lower() for tag in n.get("tags", []))):
            results.append(n)
    return sorted(results, key=lambda n: n.get("updated_at", ""), reverse=True)
