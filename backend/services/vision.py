# backend/services/vision.py
import base64
import numpy as np
from backend.models import FaceResult, VisionFrameResult
from backend.services.memory import add_emotion_record


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

    # MVP: 返回空结果，后续接入真实模型
    # 真实实现将使用 OpenCV + face detection model
    return VisionFrameResult(faces=[], fall_detected=False, timestamp=time.time())