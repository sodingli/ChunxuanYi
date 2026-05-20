from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="椿萱·颐 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由将在后续Task中逐个挂载
from backend.routers import chat, reminder, vision, voice
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reminder.router, prefix="/api/reminder", tags=["reminder"])
app.include_router(vision.router, prefix="/api/vision", tags=["vision"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])

# 静态文件服务前端
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.on_event("startup")
async def startup():
    from backend.config import PERSONAS_DIR, MEMORIES_DIR, EMOTIONS_DIR, DATA_DIR
    os.makedirs(PERSONAS_DIR, exist_ok=True)
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    os.makedirs(EMOTIONS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)