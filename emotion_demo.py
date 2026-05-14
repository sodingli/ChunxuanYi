#!/usr/bin/env python3
"""
椿萱·颐 - 情绪识别 & 对话 Demo

用法:
  python emotion_demo.py test   # 跑测试用例
  python emotion_demo.py chat   # 交互聊天
"""

import json
import os
import sys

import requests

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
TIMEOUT = 30


def call_qwen(prompt: str) -> str:
    """调用通义千问API，返回回复文本"""
    if not API_KEY:
        return "错误：请设置环境变量 DASHSCOPE_API_KEY"

    payload = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"max_tokens": 300, "temperature": 0.7},
    }

    try:
        resp = requests.post(
            API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if "output" in data and "text" in data["output"]:
            return data["output"]["text"]
        elif "code" in data:
            return f"错误：{data.get('code')} - {data.get('message')}"
        else:
            return f"未知响应: {resp.text[:200]}"

    except requests.Timeout:
        return "错误：请求超时，请稍后重试"
    except requests.RequestException as e:
        return f"错误：网络请求失败 - {e}"


def analyze_emotion(user_input: str) -> str:
    """分析情绪并返回结果"""
    prompt = f"""分析情绪，返回JSON：
用户输入：「{user_input}」

返回格式：
{{
  "emotion": "happy/sad/anxious/calm/angry/neutral",
  "emotion_cn": "开心/悲伤/焦虑/平静/愤怒/中性",
  "suggested_response": "建议回复（30字内，温暖，适合老人）"
}}

只返回JSON："""
    return call_qwen(prompt)


def chat_reply(user_input: str) -> str:
    """生成对话回复"""
    prompt = f"""你是「颐」，AI陪伴机器人，陪伴独居老人。
要求：温暖、亲切，称呼用爷爷/奶奶/您，句子短，50字内。

老人说：「{user_input}」

回复："""
    return call_qwen(prompt)


def test_emotion_analysis():
    """测试情绪分析"""
    print("=" * 60)
    print("测试1：情绪分析")
    print("=" * 60)

    test_cases = [
        "今天感觉有点累，不想动",
        "我很好，今天去公园散步了",
        "有点担心明天的检查",
        "谢谢你想着我",
    ]

    for text in test_cases:
        print(f"\n输入: {text}")
        result = analyze_emotion(text)
        try:
            data = json.loads(result)
            print(f"  情绪: {data.get('emotion_cn', 'N/A')}")
            print(f"  建议回复: {data.get('suggested_response', 'N/A')}")
        except (json.JSONDecodeError, TypeError):
            print(f"  原始回复: {result[:100]}")


def test_chat():
    """测试对话"""
    print("\n" + "=" * 60)
    print("测试2：对话模式")
    print("=" * 60)

    test_cases = [
        "今天天气不错啊",
        "我有点孤单",
        "晚饭吃什么好呢",
    ]

    for text in test_cases:
        print(f"\n老人: {text}")
        result = chat_reply(text)
        print(f"颐: {result}")


def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("椿萱·颐 - 交互模式")
    print("=" * 60)
    print("输入文字和「颐」聊天，输入 q 退出\n")

    while True:
        try:
            user_input = input("你（模拟老人）: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("q", "quit", "exit"):
            print("再见！")
            break

        if not user_input:
            continue

        result = chat_reply(user_input)
        print(f"颐: {result}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_emotion_analysis()
        test_chat()
    elif len(sys.argv) > 1 and sys.argv[1] == "chat":
        interactive_mode()
    else:
        print("用法:")
        print("  python3 emotion_demo.py test   # 跑测试用例")
        print("  python3 emotion_demo.py chat   # 交互聊天")
