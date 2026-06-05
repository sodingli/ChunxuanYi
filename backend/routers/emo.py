from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.models_schemas.emo import EmoDetectRequest, EmoDetectionResult, FaceEmotion
from backend.services.emo_detector import EmoDetector
from backend.services.emotion_agent import EmotionAnalyzer, InteractionStrategy, InteractionDecision, ResponseGenerator
from backend.services.memory import get_persona
from backend.config import EMO_MODEL_CONFIG, EMOTION_CN_MAP, EMOTION_CATEGORIES
import base64
import cv2
import numpy as np
import time

router = APIRouter()

# 全局检测器实例（单例）
_detector = None
_emotion_agent = {
    "analyzer": EmotionAnalyzer(),
    "strategy": InteractionStrategy(),
    "decision": InteractionDecision(),
    "generator": ResponseGenerator(),
    "last_trigger_time": 0,
    "last_category": None
}


def get_detector() -> EmoDetector:
    """获取检测器单例"""
    global _detector
    if _detector is None:
        _detector = EmoDetector(
            model_path=EMO_MODEL_CONFIG["model_path"],
            device=EMO_MODEL_CONFIG["device"]
        )
    return _detector


@router.post("/detect", response_model=EmoDetectionResult)
async def detect_emotion(req: EmoDetectRequest):
    """单帧情绪检测"""
    try:
        # 解码base64图像
        img_data = base64.b64decode(req.frame.split(",")[-1] if "," in req.frame else req.frame)
        arr = np.frombuffer(img_data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # 检测情绪
        detector = get_detector()
        result = detector.detect_emotion(frame)

        if not result:
            return EmoDetectionResult(faces=[], timestamp=time.time())

        # 转换为API响应格式
        faces = []
        dominant = None
        for face_data in result["faces"]:
            # 计算情绪元数据
            emotions_full = face_data["emotions"]
            primary_emotion = max(emotions_full, key=emotions_full.get)
            primary_score = emotions_full[primary_emotion]

            # 确定类别
            category = _get_emotion_category(primary_emotion)

            # 计算强度
            if primary_score > 0.7:
                intensity = "强烈"
            elif primary_score > 0.5:
                intensity = "中等"
            else:
                intensity = "轻微"

            # 实时打印检测结果
            top3_emotions = sorted(emotions_full.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"[EMO] Detection: {EMOTION_CN_MAP.get(primary_emotion, primary_emotion)}({primary_score:.2%}) | "
                  f"Top3: {', '.join([f'{EMOTION_CN_MAP.get(e, e)}:{s:.1%}' for e, s in top3_emotions])} | "
                  f"Category: {category}, Intensity: {intensity}")

            # 添加到Agent分析器
            _emotion_agent["analyzer"].add_emotion({
                "primary": primary_emotion,
                "score": primary_score,
                "category": category,
                "timestamp": time.time()
            })

            # 获取主导情绪和趋势
            dominant = _emotion_agent["analyzer"].get_dominant_emotion()
            trend = _emotion_agent["analyzer"].detect_change_pattern()

            # 打印滑动窗口状态
            if dominant:
                window_size = len(_emotion_agent["analyzer"].emotion_history)
                print(f"[EMO] Window: {window_size}/10 frames | "
                      f"Dominant: {EMOTION_CN_MAP.get(dominant['emotion'], dominant['emotion'])}({dominant['ratio']:.1%}) | "
                      f"Trend: {trend}")

            face_emotion = FaceEmotion(
                box=face_data["box"],
                emotions_full=emotions_full,
                primary_emotion=primary_emotion,
                emotion_cn=EMOTION_CN_MAP.get(primary_emotion, primary_emotion),
                category=category,
                intensity=intensity,
                trend=trend
            )

            faces.append(face_emotion)

        # 检查是否触发Agent
        agent_message = None
        if dominant:
            agent_message = await _check_and_trigger_agent(req.session_id, dominant)

        return EmoDetectionResult(
            faces=faces,
            timestamp=result["timestamp"],
            agent_message=agent_message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


async def _check_and_trigger_agent(session_id: str, emotion_state: dict) -> Optional[str]:
    """检查并触发Agent"""
    # 添加持续时间
    emotion_state["duration"] = _emotion_agent["analyzer"].get_duration()

    # 决策是否触发
    should_trigger = _emotion_agent["decision"].should_trigger(
        emotion_state=emotion_state,
        last_trigger_time=_emotion_agent["last_trigger_time"],
        user_speaking=False  # TODO: 从前端获取用户状态
    )

    if not should_trigger:
        return None

    # 选择策略
    strategy = _emotion_agent["strategy"].select_strategy(emotion_state)

    # 生成话术
    persona = get_persona(session_id)
    context = {
        "emotion": emotion_state["emotion"],
        "emotion_cn": EMOTION_CN_MAP.get(emotion_state["emotion"], emotion_state["emotion"]),
        "intensity": "强烈" if emotion_state["avg_score"] > 0.7 else "中等",
        "duration": emotion_state["duration"]
    }

    response = await _emotion_agent["generator"].generate_response(
        emotion=emotion_state["emotion"],
        strategy=strategy,
        persona=persona,
        context=context
    )

    # 更新触发状态
    _emotion_agent["last_trigger_time"] = time.time()
    _emotion_agent["last_category"] = emotion_state["category"]

    print(f"[Agent] Triggered: {strategy} -> {response}")
    return response


def _get_emotion_category(emotion: str) -> str:
    """获取情绪类别"""
    for category, emotions in EMOTION_CATEGORIES.items():
        if emotion in emotions:
            return category
    return "NEUTRAL"


@router.get("/model-info")
async def get_model_info():
    """获取模型信息"""
    detector = get_detector()
    return detector.get_model_info()


