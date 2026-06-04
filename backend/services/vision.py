# backend/services/vision.py
import base64
import numpy as np
import cv2
from backend.models import FaceResult, VisionFrameResult
from backend.services.memory import add_emotion_record
from backend.services.local_emotion import local_emotion_detector


async def detect_frame(frame_b64: str) -> VisionFrameResult:
    """处理单帧图像，返回人脸+跌倒检测结果。

    MVP阶段：使用简单占位逻辑。
    后续可接入 OpenCV + RetinaFace + YOLOv8-Pose。
    """
    import time

    # 解码base64获取图像尺寸（用于判断是否有效帧）
    try:
        img_bytes = base64.b64decode(frame_b64.split(",")[-1] if "," in frame_b64 else frame_b64)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
    except Exception:
        return VisionFrameResult(faces=[], fall_detected=False, timestamp=time.time())

    # 解码为OpenCV图像
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return VisionFrameResult(faces=[], fall_detected=False, timestamp=time.time())

    # 检测情绪（使用本地模型）
    if local_emotion_detector is not None:
        try:
            emotion_result = local_emotion_detector.process_video_frame(img)
            if emotion_result:
                face_result = FaceResult(
                    box=[0, 0, img.shape[1], img.shape[0]],  # 简单的边界框
                    emotion=emotion_result["emotion"],
                    confidence=emotion_result["confidence"]
                )
                return VisionFrameResult(
                    faces=[face_result],
                    fall_detected=False,
                    timestamp=emotion_result["timestamp"]
                )
        except Exception as e:
            print(f"情绪检测错误: {e}")

    return VisionFrameResult(faces=[], fall_detected=False, timestamp=time.time())


async def detect_emotion_from_frame(frame_b64: str) -> dict:
    """从图像帧检测情绪（使用本地模型）"""
    import time
    import cv2

    # 解码base64
    try:
        img_bytes = base64.b64decode(frame_b64.split(",")[-1] if "," in frame_b64 else frame_b64)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
    except Exception:
        return {
            "emotion": "neutral",
            "emotion_cn": "中性",
            "confidence": 0.0,
            "timestamp": time.time()
        }

    # 解码为OpenCV图像
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {
            "emotion": "neutral",
            "emotion_cn": "中性",
            "confidence": 0.0,
            "timestamp": time.time()
        }

    # 使用本地情绪检测器
    if local_emotion_detector is not None:
        try:
            emotion_result = local_emotion_detector.process_video_frame(img)
            if emotion_result:
                return emotion_result
        except Exception as e:
            print(f"情绪检测错误: {e}")

    return {
        "emotion": "neutral",
        "emotion_cn": "中性",
        "confidence": 0.0,
        "timestamp": time.time()
    }