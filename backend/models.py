from pydantic import BaseModel
from typing import Optional


# --- Chat ---
class ChatRequest(BaseModel):
    user_input: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    emotion: str


class EmotionRequest(BaseModel):
    text: str


class EmotionResponse(BaseModel):
    emotion: str
    emotion_cn: str
    suggested_response: str


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    address_as: Optional[str] = None
    style: Optional[str] = None
    custom_instructions: Optional[str] = None


class Persona(BaseModel):
    name: str = "颐"
    gender: str = "neutral"
    personality: str = "温暖、耐心、有同理心"
    address_as: str = "爷爷"
    style: str = "句子短，不用网络用语，50字内"
    custom_instructions: str = "主动关心身体和饮食"


# --- Vision ---
class FaceResult(BaseModel):
    box: list[int]
    emotion: str
    confidence: float


class VisionFrameResult(BaseModel):
    faces: list[FaceResult]
    fall_detected: bool
    timestamp: float


# --- Voice ---
class AsrRequest(BaseModel):
    audio: str
    format: str = "wav"


class AsrResponse(BaseModel):
    text: str
    emotion: str
    emotion_confidence: float
    emotion_source: str = "voice"


class TtsRequest(BaseModel):
    text: str


# --- Reminder ---
class ReminderCreate(BaseModel):
    content: str
    date: str
    is_health: bool = False


class ReminderItem(BaseModel):
    id: int
    content: str
    date: str
    is_health: bool = False
    completed: bool = False


# --- Memory ---
class MemoryCreate(BaseModel):
    content: str
    mtype: str = "conversation"


class MemoryItem(BaseModel):
    id: int
    content: str
    mtype: str
    timestamp: str