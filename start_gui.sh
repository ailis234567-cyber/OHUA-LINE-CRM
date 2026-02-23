#!/bin/bash
# 启动 GUI 界面

cd "$(dirname "$0")"
source venv/bin/activate
python gui.py

