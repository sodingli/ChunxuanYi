#!/bin/bash
# 椿萱·颐 - Demo运行脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查依赖
if ! python3 -c "import requests" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

if [ "$1" = "test" ]; then
    python3 emotion_demo.py test
elif [ "$1" = "chat" ]; then
    python3 emotion_demo.py chat
elif [ "$1" = "sim" ]; then
    open yi_device_simulator.html
else
    echo "用法:"
    echo "  ./run_demo.sh test   # 跑测试用例"
    echo "  ./run_demo.sh chat   # 交互聊天"
    echo "  ./run_demo.sh sim    # 打开浏览器模拟器"
fi
