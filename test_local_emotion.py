#!/usr/bin/env python3
"""直接测试本地情绪检测功能"""
import cv2
import numpy as np
from backend.services.local_emotion import LocalEmotionDetector

def test_local_emotion_detector():
    print("测试本地情绪检测器...")

    # 创建检测器实例
    detector = LocalEmotionDetector()

    if detector is None:
        print("✗ 检测器初始化失败")
        return False

    print("✓ 检测器初始化成功")

    # 创建测试图像（白色矩形代表人脸）
    test_img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(test_img, (50, 50), (150, 150), (255, 255, 255), -1)

    print("测试图像创建成功，开始情绪检测...")

    try:
        # 测试情绪检测
        result = detector.process_video_frame(test_img)

        if result:
            print("✓ 情绪检测成功")
            print(f"  情绪: {result['emotion']}")
            print(f"  中文情绪: {result.get('emotion_cn', '')}")
            print(f"  置信度: {result['confidence']:.2f}")
            print(f"  时间戳: {result['timestamp']}")
            return True
        else:
            print("✗ 情绪检测返回None")
            return False

    except Exception as e:
        print(f"✗ 情绪检测过程中出错: {e}")
        return False

if __name__ == "__main__":
    test_local_emotion_detector()