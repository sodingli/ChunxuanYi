# backend/routers/reminder.py
from fastapi import APIRouter, HTTPException
from backend.models import ReminderCreate, ReminderItem, MemoryCreate, MemoryItem
from backend.services.reminder import get_reminders, add_reminder, delete_reminder, check_due_reminders
from backend.services.memory import get_memories, add_memory, get_emotion_records

router = APIRouter()


# --- Reminders ---
@router.get("", response_model=list[ReminderItem])
async def list_reminders(is_health: bool = False):
    return get_reminders(is_health)


@router.post("", response_model=ReminderItem)
async def create_reminder(req: ReminderCreate):
    return add_reminder(req.content, req.date, req.is_health)


@router.delete("/{reminder_id}")
async def remove_reminder(reminder_id: int, is_health: bool = False):
    if not delete_reminder(reminder_id, is_health):
        raise HTTPException(status_code=404, detail="提醒不存在")


@router.get("/health", response_model=list[ReminderItem])
async def list_health_reminders():
    return get_reminders(is_health=True)


@router.post("/health", response_model=ReminderItem)
async def create_health_reminder(req: ReminderCreate):
    return add_reminder(req.content, req.date, is_health=True)


@router.get("/check", response_model=list[ReminderItem])
async def check_reminders():
    return check_due_reminders()


# --- Memory ---
@router.get("/memories", response_model=list[MemoryItem])
async def list_memories(session_id: str = "default"):
    raw = get_memories(session_id)
    return [MemoryItem(id=m["id"], content=m["content"], mtype=m["type"], timestamp=m["timestamp"]) for m in raw]


@router.post("/memories", response_model=MemoryItem)
async def create_memory(req: MemoryCreate, session_id: str = "default"):
    item = add_memory(session_id, req.content, req.mtype)
    return MemoryItem(**item)


# --- Emotion Records ---
@router.get("/emotions", response_model=list[dict])
async def list_emotions(date: str | None = None):
    return get_emotion_records(date)