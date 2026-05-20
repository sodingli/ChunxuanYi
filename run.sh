#!/bin/bash
cd "$(dirname "$0")"
echo "启动椿萱·颐后端服务..."
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000