#!/usr/bin/env python3
"""
测试 Web 应用是否能正常启动
"""

import sys

print("=" * 50)
print("🔍 检查依赖...")
print("=" * 50)

# 检查 Flask
try:
    import flask
    print(f"✅ Flask 已安装 (版本: {flask.__version__})")
except ImportError:
    print("❌ Flask 未安装")
    print("请运行: pip install flask")
    sys.exit(1)

# 检查其他依赖
try:
    import yaml
    print("✅ PyYAML 已安装")
except ImportError:
    print("❌ PyYAML 未安装")
    print("请运行: pip install pyyaml")
    sys.exit(1)

# 检查文件
import os
from pathlib import Path

print("\n" + "=" * 50)
print("📁 检查文件...")
print("=" * 50)

files_to_check = [
    "web_app.py",
    "templates/index.html",
    "static/css/style.css",
    "config.yaml",
    "screenshots"
]

for file in files_to_check:
    if Path(file).exists():
        print(f"✅ {file} 存在")
    else:
        print(f"⚠️  {file} 不存在")

# 检查 screenshots 目录
screenshots_dir = Path("screenshots")
if screenshots_dir.exists():
    id_folders = [d for d in screenshots_dir.iterdir() if d.is_dir() and d.name.startswith('ID_')]
    print(f"✅ screenshots 目录存在，找到 {len(id_folders)} 个ID文件夹")
else:
    print("⚠️  screenshots 目录不存在")

print("\n" + "=" * 50)
print("🚀 尝试启动 Web 应用...")
print("=" * 50)

try:
    from web_app import app
    print("✅ Web 应用导入成功")
    print("\n📝 启动命令:")
    print("   python web_app.py")
    print("\n或者:")
    print("   ./start_web.sh")
    print("\n然后访问: http://localhost:5000")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ 所有检查通过！")
print("=" * 50)

