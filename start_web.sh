#!/bin/bash
# 启动 Web 应用

cd "$(dirname "$0")"
source venv/bin/activate
python web_app.py

