# backend/routers/vision.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.models import VisionFrameResult
from backend.services.vision import detect_frame
import asyncio
import json

router = APIRouter()


@router.post("/detect", response_model=VisionFrameResult)
async def detect_single_frame(frame_b64: str):
    return await detect_frame(frame_b64)


@router.websocket("/stream")
async def vision_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame_b64 = json.loads(data).get("frame", "")
            if not frame_b64:
                continue
            result = await detect_frame(frame_b64)
            await websocket.send_text(result.model_dump_json())
    except WebSocketDisconnect:
        pass
    except Exception:
        pass