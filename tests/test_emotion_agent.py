import pytest
import time
from backend.services.emotion_agent import EmotionAnalyzer, InteractionStrategy, InteractionDecision, ResponseGenerator
from backend.config import EMOTION_AGENT_CONFIG

@pytest.fixture
def analyzer():
    """创建分析器实例"""
    return EmotionAnalyzer(window_size=10)

def test_emotion_analyzer_initialization(analyzer):
    """测试分析器初始化"""
    assert analyzer.window_size == 10
    assert len(analyzer.emotion_history) == 0

def test_add_emotion(analyzer):
    """测试添加情绪数据"""
    emotion_data = {
        "primary": "Happiness",
        "score": 0.8,
        "category": "POSITIVE",
        "timestamp": time.time()
    }
    analyzer.add_emotion(emotion_data)
    assert len(analyzer.emotion_history) == 1

def test_get_dominant_emotion(analyzer):
    """测试获取主导情绪"""
    # 添加多个情绪
    for _ in range(7):
        analyzer.add_emotion({
            "primary": "Happiness",
            "score": 0.8,
            "category": "POSITIVE",
            "timestamp": time.time()
        })
    for _ in range(3):
        analyzer.add_emotion({
            "primary": "Neutral",
            "score": 0.6,
            "category": "NEUTRAL",
            "timestamp": time.time()
        })

    dominant = analyzer.get_dominant_emotion()
    assert dominant["emotion"] == "Happiness"
    assert dominant["category"] == "POSITIVE"
    assert dominant["ratio"] == 0.7  # 7/10

def test_calculate_stability(analyzer):
    """测试稳定性计算"""
    # 添加稳定情绪
    for _ in range(10):
        analyzer.add_emotion({
            "primary": "Calm",
            "score": 0.75,
            "category": "POSITIVE",
            "timestamp": time.time()
        })

    stability = analyzer.calculate_stability()
    assert stability == 1.0  # 完全稳定

