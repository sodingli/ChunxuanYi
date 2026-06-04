#!/usr/bin/env python3
"""测试本地情绪识别功能"""
import cv2
import numpy as np
import base64
import requests
import time

# 创建一个简单的测试图像（纯色）
def create_test_image():
    # 创建一个黑色图像
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    # 在中间画一个白色矩形代表人脸
    cv2.rectangle(img, (50, 50), (150, 150), (255, 255, 255), -1)
    return img

# 将图像转换为base64
def image_to_base64(img):
    _, buffer = cv2.imencode('.jpg', img)
    img_bytes = buffer.tobytes()
    return base64.b64encode(img_bytes).decode('utf-8')

# 测试情绪检测
def test_emotion_detection():
    print("测试情绪检测功能...")

    # 创建测试图像
    test_img = create_test_image()
    base64_img = image_to_base64(test_img)

    # 调用API
    try:
        response = requests.post(
            "http://localhost:8000/api/vision/emotion",
            json={"frame": f"data:image/jpeg;base64,{base64_img}"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ 情绪检测成功")
            print(f"  情绪: {result.get('emotion', '未知')}")
            print(f"  中文情绪: {result.get('emotion_cn', '未知')}")
            print(f"  置信度: {result.get('confidence', 0):.2f}")
            print(f"  时间戳: {result.get('timestamp', 0)}")
            return True
        else:
            print(f"✗ 情绪检测失败: {response.status_code}")
            print(f"  错误: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    test_emotion_detection()