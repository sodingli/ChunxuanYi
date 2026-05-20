# backend/services/reminder.py
import json
import os
import time
from backend.config import REMINDERS_FILE
from backend.models import ReminderItem


def _read_reminders() -> dict:
    if not os.path.exists(REMINDERS_FILE):
        return {"reminders": [], "health": []}
    with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_reminders(data: dict):
    os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_reminders(is_health: bool = False) -> list[ReminderItem]:
    data = _read_reminders()
    key = "health" if is_health else "reminders"
    return [ReminderItem(**r) for r in data.get(key, [])]


def add_reminder(content: str, date: str, is_health: bool = False) -> ReminderItem:
    data = _read_reminders()
    key = "health" if is_health else "reminders"
    item = ReminderItem(id=int(time.time() * 1000), content=content, date=date, is_health=is_health)
    data.setdefault(key, []).append(item.model_dump())
    _write_reminders(data)
    return item


def delete_reminder(reminder_id: int, is_health: bool = False) -> bool:
    data = _read_reminders()
    key = "health" if is_health else "reminders"
    items = data.get(key, [])
    before = len(items)
    data[key] = [r for r in items if r["id"] != reminder_id]
    _write_reminders(data)
    return len(data[key]) < before


def check_due_reminders() -> list[ReminderItem]:
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    data = _read_reminders()
    due = []
    for key in ["reminders", "health"]:
        for r in data.get(key, []):
            if not r.get("completed") and r.get("date") == today:
                due.append(ReminderItem(**r))
                r["completed"] = True
    _write_reminders(data)
    return due