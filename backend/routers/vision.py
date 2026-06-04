# backend/routers/vision.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from backend.models import VisionFrameResult, EmotionDetectionResult
from backend.services.vision import detect_frame, detect_emotion_from_frame
from backend.config import PROACTIVE_CARE_TEMPLATE_PATH
import asyncio
import json
import os

router = APIRouter()


def _load_prompt_template(template_path: str) -> str:
    """加载提示词模板文件"""
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


@router.post("/detect", response_model=VisionFrameResult)
async def detect_single_frame(frame_b64: str):
    return await detect_frame(frame_b64)


@router.post("/emotion")
async def detect_emotion(data: dict):
    """检测图像中的情绪，并在情绪异常时触发主动关怀"""
    frame = data.get("frame", "")
    session_id = data.get("session_id", "default")

    try:
        result = await detect_emotion_from_frame(frame)
        emotion = result.get("emotion", "neutral")
        confidence = result.get("confidence", 0.0)

        # 触发条件：悲伤/愤怒/恐惧 且置信度>0.6
        should_trigger = emotion in ["sad", "angry", "fearful"] and confidence > 0.6

        proactive_message = None
        if should_trigger:
            from backend.services.llm import call_qwen
            from backend.services.memory import get_persona

            persona = get_persona(session_id)
            emotion_map = {"sad": "悲伤", "angry": "生气", "fearful": "恐惧"}
            emotion_cn = emotion_map.get(emotion, emotion)

            # 从模板文件加载提示词
            template = _load_prompt_template(PROACTIVE_CARE_TEMPLATE_PATH)
            if not template:
                # 兜底：使用硬编码模板
                template = """你是「{name}」，发现老人情绪{emotion_cn}，主动关心：
- 语气温暖、关切
- 不超过30字
- 不要问"怎么了"，直接表达关心
- {style}

直接回复关怀的话："""

            prompt = template.format(
                name=persona.name,
                emotion_cn=emotion_cn,
                address_as=persona.address_as,
                style=persona.style
            )

            try:
                proactive_message = await call_qwen(prompt, max_tokens=100)
            except Exception:
                proactive_message = None

        return {
            **result,
            "should_trigger": should_trigger,
            "proactive_message": proactive_message
        }
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