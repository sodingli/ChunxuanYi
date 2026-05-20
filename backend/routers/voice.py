# backend/routers/voice.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.models import AsrRequest, AsrResponse, TtsRequest
from backend.services.asr import recognize_speech, analyze_voice_emotion
from backend.services.tts import synthesize_speech
import json

router = APIRouter()


@router.post("/asr", response_model=AsrResponse)
async def asr(req: AsrRequest):
    result = await recognize_speech(req.audio, req.format)
    if result["text"]:
        emotion = await analyze_voice_emotion(result["text"])
        result["emotion"] = emotion["emotion"]
        result["emotion_confidence"] = emotion["emotion_confidence"]
    return AsrResponse(**result)


@router.post("/tts")
async def tts(req: TtsRequest):
    return await synthesize_speech(req.text)


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # MVP: 占位，后续接入实时ASR
            await websocket.send_text(json.dumps({
                "text": "",
                "emotion": "neutral",
                "emotion_confidence": 0.5,
                "emotion_source": "voice",
            }))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass