#!/usr/bin/env python3
"""测试所有API端点是否正常工作"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_chat():
    """测试对话API"""
    print("1. 测试对话API...")
    try:
        resp = requests.post(f"{BASE_URL}/chat", json={"user_input": "你好", "session_id": "test"})
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ 成功: {data['reply'][:50]}...")
            return True
        else:
            print(f"   ✗ 失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False

def test_persona():
    """测试角色API"""
    print("2. 测试角色API...")
    try:
        # 获取角色
        resp = requests.get(f"{BASE_URL}/chat/persona?session_id=test")
        if resp.status_code == 200:
            persona = resp.json()
            print(f"   ✓ 当前角色: {persona['name']}")

            # 更新角色
            update_data = {
                "name": "测试助手",
                "gender": "female",
                "personality": "活泼可爱",
                "address_as": "姐姐",
                "style": "可爱活泼"
            }
            resp = requests.put(f"{BASE_URL}/chat/persona?session_id=test", json=update_data)
            if resp.status_code == 200:
                print("   ✓ 角色更新成功")
                return True
            else:
                print(f"   ✗ 角色更新失败: {resp.status_code}")
                return False
        else:
            print(f"   ✗ 获取角色失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False

def test_reminders():
    """测试提醒API"""
    print("3. 测试提醒API...")
    try:
        # 添加提醒
        reminder_data = {"content": "测试提醒", "date": "2026-05-20"}
        resp = requests.post(f"{BASE_URL}/reminder", json=reminder_data)
        if resp.status_code == 200:
            reminder = resp.json()
            print(f"   ✓ 添加提醒成功: {reminder['id']}")

            # 获取提醒列表
            resp = requests.get(f"{BASE_URL}/reminder")
            if resp.status_code == 200:
                reminders = resp.json()
                print(f"   ✓ 获取到 {len(reminders)} 个提醒")
                return True
            else:
                print(f"   ✗ 获取提醒失败: {resp.status_code}")
                return False
        else:
            print(f"   ✗ 添加提醒失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False

def test_vision():
    """测试视觉API"""
    print("4. 测试视觉API...")
    try:
        # 测试情绪检测（发送空数据）
        resp = requests.post(f"{BASE_URL}/vision/emotion", json={"frame": ""})
        if resp.status_code == 200:
            print("   ✓ 视觉API正常响应")
            return True
        else:
            print(f"   ✗ 视觉API失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False

def test_voice():
    """测试语音API"""
    print("5. 测试语音API...")
    try:
        # 测试ASR
        resp = requests.post(f"{BASE_URL}/voice/asr", json={"audio": "", "format": "wav"})
        if resp.status_code == 200:
            print("   ✓ 语音API正常响应")
            return True
        else:
            print(f"   ✗ 语音API失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False

def main():
    print("开始测试所有API端点...\n")

    tests = [
        test_chat,
        test_persona,
        test_reminders,
        test_vision,
        test_voice
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print(f"测试结果: {passed}/{len(tests)} 通过")

    if passed == len(tests):
        print("✓ 所有API测试通过！")
    else:
        print("✗ 部分API测试失败，请检查服务状态")

if __name__ == "__main__":
    main()