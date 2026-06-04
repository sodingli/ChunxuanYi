import pytest
from backend.models_schemas.emo import EmotionScore, FaceEmotion, EmoDetectionResult

def test_emotion_score_creation():
    """测试情绪分数模型"""
    score = EmotionScore(name="Happiness", name_cn="快乐", score=0.85)
    assert score.name == "Happiness"
    assert score.name_cn == "快乐"
    assert score.score == 0.85

def test_face_emotion_with_top_emotions():
    """测试人脸情绪模型"""
    emotions_full = {"Happiness": 0.6, "Calm": 0.3, "Neutral": 0.1}
    face = FaceEmotion(
        box=[100, 100, 300, 300],
        emotions_full=emotions_full,
        primary_emotion="Happiness",
        emotion_cn="快乐",
        category="POSITIVE",
        intensity="中等",
        trend="STABLE"
    )
    assert len(face.top_emotions) == 3
    assert face.top_emotions[0].name == "Happiness"
    assert face.top_emotions[0].score == 0.6

def test_emo_detection_result():
    """测试检测结果模型"""
    result = EmoDetectionResult(
        faces=[],
        timestamp=1234567890.123
    )
    assert result.faces == []
    assert result.timestamp == 1234567890.123
