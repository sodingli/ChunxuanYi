import pytest
from fastapi.testclient import TestClient
from backend.main import app
import base64
import cv2
import numpy as np

client = TestClient(app)

def create_test_frame():
    """创建测试图像"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (200, 150), (440, 330), (255, 255, 255), -1)
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def test_emo_detect_endpoint():
    """测试EMO检测端点"""
    frame_b64 = create_test_frame()
    response = client.post("/api/emo/detect", json={
        "frame": frame_b64,
        "session_id": "test"
    })
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert "timestamp" in data
    assert "agent_message" in data

def test_model_info_endpoint():
    """测试模型信息端点"""
    response = client.get("/api/emo/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_path" in data
    assert "device" in data
    assert data["loaded"] is True
