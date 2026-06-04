from collections import deque
from typing import Dict, List, Optional
import time
from backend.config import EMOTION_AGENT_CONFIG, EMOTION_CATEGORIES


class EmotionAnalyzer:
    """情绪分析器 - 维护滑动窗口，分析情绪模式"""

    def __init__(self, window_size: int = None):
        """
        初始化分析器

        Args:
            window_size: 滑动窗口大小（帧数）
        """
        self.window_size = window_size or EMOTION_AGENT_CONFIG["window_size"]
        self.emotion_history = deque(maxlen=self.window_size)

    def add_emotion(self, emotion_data: Dict):
        """
        添加情绪数据到滑动窗口

        Args:
            emotion_data: 包含primary, score, category, timestamp的字典
        """
        self.emotion_history.append(emotion_data)

    def get_dominant_emotion(self) -> Optional[Dict]:
        """
        获取窗口内的主导情绪

        Returns:
            {
                "emotion": str,
                "category": str,
                "ratio": float,  # 占比
                "avg_score": float
            }
        """
        if not self.emotion_history:
            return None

        # 统计情绪出现次数
        emotion_counts = {}
        emotion_scores = {}

        for data in self.emotion_history:
            emotion = data["primary"]
            score = data["score"]

            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)

        # 找出最频繁的情绪
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        count = emotion_counts[dominant_emotion]
        ratio = count / len(self.emotion_history)
        avg_score = sum(emotion_scores[dominant_emotion]) / len(emotion_scores[dominant_emotion])

        # 确定类别
        category = self._get_emotion_category(dominant_emotion)

        return {
            "emotion": dominant_emotion,
            "category": category,
            "ratio": ratio,
            "avg_score": avg_score
        }

    def calculate_stability(self) -> float:
        """
        计算情绪稳定性

        Returns:
            稳定性分数 (0-1)，1表示完全稳定
        """
        if len(self.emotion_history) < 2:
            return 1.0

        # 计算主导情绪的占比
        dominant = self.get_dominant_emotion()
        if not dominant:
            return 0.0

        return dominant["ratio"]

    def detect_change_pattern(self) -> str:
        """
        检测情绪变化模式

        Returns:
            "STABLE" | "GRADUAL" | "RAPID"
        """
        stability = self.calculate_stability()

        if stability >= 0.8:
            return "STABLE"
        elif stability >= 0.5:
            return "GRADUAL"
        else:
            return "RAPID"

    def _get_emotion_category(self, emotion: str) -> str:
        """获取情绪类别"""
        for category, emotions in EMOTION_CATEGORIES.items():
            if emotion in emotions:
                return category
        return "NEUTRAL"

    def get_duration(self) -> float:
        """
        获取主导情绪持续时间（秒）

        Returns:
            持续时间
        """
        if len(self.emotion_history) < 2:
            return 0.0

        first_time = self.emotion_history[0]["timestamp"]
        last_time = self.emotion_history[-1]["timestamp"]
        return last_time - first_time

