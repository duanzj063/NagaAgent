#!/bin/bash
# Live2D启动脚本
echo "启动NagaAgent Live2D..."

# 激活虚拟环境
.venv/bin/activate.ps1   

# 运行Live2D测试
echo "运行Live2D测试..."
python test_live2d_simple.py

if [ $? -eq 0 ]; then
    echo "✅ Live2D测试通过，启动主程序..."
    python main.py
else
    echo "❌ Live2D测试失败"
    exit 1
fi