import pytest
import numpy as np
from backend.services.emo_detector import EmoDetector
from backend.config import EMO_MODEL_CONFIG

@pytest.fixture
def detector():
    """创建检测器实例"""
    return EmoDetector(EMO_MODEL_CONFIG["model_path"])

def test_detector_initialization(detector):
    """测试检测器初始化"""
    assert detector.model is not None
    assert detector.device in ["cpu", "cuda"]

def test_get_model_info(detector):
    """测试获取模型信息"""
    info = detector.get_model_info()
    assert "model_path" in info
    assert "device" in info
    assert "loaded" in info

def test_detect_emotion_with_valid_frame(detector):
    """测试有效帧检测"""
    # 创建测试图像 (224x224x3)
    frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    result = detector.detect_emotion(frame)
    assert result is not None
    assert isinstance(result, dict)
