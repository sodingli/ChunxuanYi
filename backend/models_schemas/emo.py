from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import time


class EmotionScore(BaseModel):
    """单个情绪分数"""
    name: str = Field(..., description="情绪英文名")
    name_cn: str = Field(..., description="情绪中文名")
    score: float = Field(..., ge=0.0, le=1.0, description="情绪置信度")


class FaceEmotion(BaseModel):
    """单张人脸的情绪检测结果"""
    box: List[int] = Field(..., description="人脸框 [x, y, width, height]")
    emotions_full: Dict[str, float] = Field(..., description="20种情绪的完整分布")
    top_emotions: List[EmotionScore] = Field(default_factory=list, description="Top 5情绪")
    emotion_combination: Optional[str] = Field(None, description="情绪组合描述")
    primary_emotion: str = Field(..., description="主要情绪")
    emotion_cn: str = Field(..., description="主要情绪中文名")
    category: str = Field(..., description="情绪类别: POSITIVE/NEGATIVE/NEUTRAL")
    intensity: str = Field(..., description="强度: 轻微/中等/强烈")
    trend: str = Field(default="STABLE", description="趋势: STABLE/GRADUAL/RAPID")

    def __init__(self, **data):
        super().__init__(**data)
        # 自动生成top_emotions
        if not self.top_emotions and self.emotions_full:
            from backend.config import EMOTION_CN_MAP
            sorted_emotions = sorted(self.emotions_full.items(), key=lambda x: x[1], reverse=True)[:5]
            self.top_emotions = [
                EmotionScore(name=name, name_cn=EMOTION_CN_MAP.get(name, name), score=score)
                for name, score in sorted_emotions
            ]


class EmoDetectionResult(BaseModel):
    """EMO检测结果"""
    faces: List[FaceEmotion] = Field(default_factory=list, description="检测到的人脸列表")
    timestamp: float = Field(default_factory=time.time, description="时间戳")


class EmoDetectRequest(BaseModel):
    """EMO检测请求"""
    frame: str = Field(..., description="base64编码的图像")
    session_id: str = Field(default="default", description="会话ID")
