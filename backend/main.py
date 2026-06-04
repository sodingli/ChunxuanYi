from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.config import PERSONAS_DIR, MEMORIES_DIR, EMOTIONS_DIR, DATA_DIR
    os.makedirs(PERSONAS_DIR, exist_ok=True)
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    os.makedirs(EMOTIONS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    yield


app = FastAPI(title="椿萱·颐 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8008", "http://127.0.0.1:3000", "http://127.0.0.1:8008"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routers import chat, reminder, vision
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reminder.router, prefix="/api/reminder", tags=["reminder"])
app.include_router(vision.router, prefix="/api/vision", tags=["vision"])

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")