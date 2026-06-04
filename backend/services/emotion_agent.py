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


class InteractionStrategy:
    """策略选择器 - 根据情绪状态选择交互策略"""

    STRATEGIES = [
        "POSITIVE_EMPATHY",     # 积极共情
        "NEGATIVE_CARE",        # 消极关怀
        "EMOTION_TRANSITION",   # 情绪转换引导
        "MIXED_EMOTION",        # 混合情绪探索
        "SILENT_PRESENCE"       # 沉默陪伴
    ]

    def select_strategy(self, emotion_state: Dict) -> str:
        """
        选择交互策略

        Args:
            emotion_state: 情绪状态字典

        Returns:
            策略名称
        """
        category = emotion_state.get("category")
        ratio = emotion_state.get("ratio", 0)
        avg_score = emotion_state.get("avg_score", 0)

        # 情绪不够稳定，使用混合情绪策略
        if ratio < 0.7:
            return "MIXED_EMOTION"

        # 根据类别选择策略
        if category == "POSITIVE":
            return "POSITIVE_EMPATHY"
        elif category == "NEGATIVE":
            # 消极情绪根据强度选择
            if avg_score > 0.7:
                return "NEGATIVE_CARE"
            else:
                return "SILENT_PRESENCE"
        else:
            return "MIXED_EMOTION"


class InteractionDecision:
    """交互决策引擎 - 决定是否触发、何时触发"""

    def __init__(self):
        self.config = EMOTION_AGENT_CONFIG

    def should_trigger(self,
                      emotion_state: Dict,
                      last_trigger_time: float,
                      user_speaking: bool) -> bool:
        """
        判断是否应该触发交互

        Args:
            emotion_state: 情绪状态
            last_trigger_time: 上次触发时间（unix timestamp）
            user_speaking: 用户是否正在说话

        Returns:
            是否触发
        """
        # 用户正在说话时不打断
        if user_speaking:
            return False

        # 检查置信度阈值
        avg_score = emotion_state.get("avg_score", 0)
        if avg_score < self.config["trigger_threshold"]["min_confidence"]:
            return False

        # 检查持续时间
        duration = emotion_state.get("duration", 0)
        if duration < self.config["trigger_threshold"]["min_duration"]:
            return False

        # 检查稳定性
        ratio = emotion_state.get("ratio", 0)
        if ratio < self.config["trigger_threshold"]["stability_ratio"]:
            return False

        # 检查冷却时间
        current_time = time.time()
        if last_trigger_time > 0:
            elapsed = current_time - last_trigger_time
            # 这里简化处理，实际需要传入last_category
            min_cooldown = self.config["cooldown"]["different_category"]
            if elapsed < min_cooldown:
                return False

        return True

    def get_priority(self, strategy: str, intensity: float) -> int:
        """
        获取策略优先级

        Args:
            strategy: 策略名称
            intensity: 情绪强度

        Returns:
            优先级数值（越大越优先）
        """
        base_priority = self.config["priority"].get(strategy, 1)

        # 强烈情绪提升优先级
        if intensity > 0.7:
            return base_priority + 5

        return base_priority

    def calculate_cooldown(self,
                          last_category: str,
                          current_category: str,
                          intensity: float) -> float:
        """
        计算冷却时间

        Args:
            last_category: 上次情绪类别
            current_category: 当前情绪类别
            intensity: 当前情绪强度

        Returns:
            冷却时间（秒）
        """
        # 强烈情绪缩短冷却时间
        if intensity > 0.7:
            return self.config["cooldown"]["high_intensity"]

        # 同类情绪
        if last_category == current_category:
            return self.config["cooldown"]["same_category"]

        # 异类情绪（情绪转换）
        return self.config["cooldown"]["different_category"]



