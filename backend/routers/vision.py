# backend/routers/vision.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from backend.models import VisionFrameResult, EmotionDetectionResult
from backend.services.vision import detect_frame, detect_emotion_from_frame
import asyncio
import json

router = APIRouter()


@router.post("/detect", response_model=VisionFrameResult)
async def detect_single_frame(frame_b64: str):
    return await detect_frame(frame_b64)


@router.post("/emotion")
async def detect_emotion(data: dict):
    """检测图像中的情绪"""
    frame = data.get("frame", "")
    try:
        result = await detect_emotion_from_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"情绪检测失败: {str(e)}")


@router.websocket("/stream")
async def vision_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            frame_b64 = frame_data.get("frame", "")

            if not frame_b64:
                continue

            # 检测人脸和情绪
            vision_result = await detect_frame(frame_b64)
            emotion_result = await detect_emotion_from_frame(frame_b64)

            # 合并结果
            combined_result = {
                "vision": vision_result.model_dump(),
                "emotion": emotion_result,
                "timestamp": vision_result.timestamp
            }

            await websocket.send_text(json.dumps(combined_result))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass