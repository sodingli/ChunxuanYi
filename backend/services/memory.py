import json
import os
import time
from backend.config import PERSONAS_DIR, MEMORIES_DIR, EMOTIONS_DIR, DEFAULT_PERSONA
from backend.models import Persona


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_json(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- Persona ---
def get_persona(session_id: str) -> Persona:
    path = os.path.join(PERSONAS_DIR, f"{session_id}.json")
    data = _read_json(path, DEFAULT_PERSONA)
    return Persona(**data)


def update_persona(session_id: str, updates: dict) -> Persona:
    path = os.path.join(PERSONAS_DIR, f"{session_id}.json")
    current = _read_json(path, DEFAULT_PERSONA)
    current.update({k: v for k, v in updates.items() if v is not None})
    _write_json(path, current)
    return Persona(**current)


# --- Memory ---
def get_memories(session_id: str) -> list[dict]:
    path = os.path.join(MEMORIES_DIR, f"{session_id}.json")
    return _read_json(path, [])


def add_memory(session_id: str, content: str, mtype: str = "conversation") -> dict:
    path = os.path.join(MEMORIES_DIR, f"{session_id}.json")
    memories = _read_json(path, [])
    item = {"id": int(time.time() * 1000), "content": content, "type": mtype, "timestamp": _now_iso()}
    memories.append(item)
    _write_json(path, memories)
    return item


def get_memory_context(session_id: str, limit: int = 10) -> str:
    memories = get_memories(session_id)
    if not memories:
        return ""
    recent = memories[-limit:]
    return "\n【已记住的信息】：\n" + "\n".join(f"- {m['content']}" for m in recent)


# --- Emotion Records ---
def add_emotion_record(emotion: str, value: float, source: str = "vision"):
    _ensure_dir(EMOTIONS_DIR)
    date_str = _now_date()
    path = os.path.join(EMOTIONS_DIR, f"{date_str}.json")
    records = _read_json(path, [])
    records.append({"id": int(time.time() * 1000), "time": _now_time(), "emotion": emotion, "value": value, "source": source})
    _write_json(path, records)


def get_emotion_records(date: str | None = None) -> list[dict]:
    date_str = date or _now_date()
    path = os.path.join(EMOTIONS_DIR, f"{date_str}.json")
    return _read_json(path, [])


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _now_date():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def _now_time():
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")