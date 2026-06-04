#!/bin/bash
# 椿萱·颐 - 统一启动脚本
# 用法:
#   ./start.sh              启动 Node.js 后端 (默认, 端口 3000)
#   ./start.sh --all        启动 Node.js + Python 后端
#   ./start.sh --python     仅启动 Python 后端 (端口 8000)

cd "$(dirname "$0")"

MODE="${1:---node}"

case "$MODE" in
  --node|-n)
    echo "[启动] Node.js 后端 -> http://localhost:3000"
    exec node server.js
    ;;
  --python|-p)
    echo "[启动] Python 后端 -> http://localhost:8008"
    exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8008
    ;;
  --all|-a)
    echo "=========================================="
    echo "  椿萱·颐 - AI陪伴设备模拟器"
    echo "=========================================="

    if [ -z "$DASHSCOPE_API_KEY" ]; then
      echo "[提醒] 环境变量 DASHSCOPE_API_KEY 未设置"
      echo "       可在启动前设置: export DASHSCOPE_API_KEY='sk-xxx'"
      echo "       或通过前端设置页面输入"
      echo ""
    fi

    echo "[启动] Python 后端 -> http://localhost:8008"
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8008 &
    PYTHON_PID=$!

    echo "[启动] Node.js 后端 -> http://localhost:3000"
    node server.js &
    NODE_PID=$!

    echo ""
    echo "服务已启动:"
    echo "  Node.js 前端: http://localhost:3000"
    echo "  Python 前端:  http://localhost:8008"
    echo ""
    echo "按 Ctrl+C 停止所有服务"

    trap "kill $PYTHON_PID $NODE_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait
    ;;
  *)
    echo "用法: ./start.sh [--node|--python|--all]"
    echo "  --node    仅启动 Node.js 后端 (默认)"
    echo "  --python  仅启动 Python 后端"
    echo "  --all     启动 Node.js + Python 后端"
    exit 1
    ;;
esac
