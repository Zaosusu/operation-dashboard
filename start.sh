#!/bin/bash

# Operation Dashboard - 作战仪表盘 启动脚本
# 支持 macOS / Linux

echo "========================================"
echo "  Operation Dashboard - 作战仪表盘"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未检测到Python，请先安装Python 3.7+"
        echo "macOS: brew install python3"
        echo "Linux: sudo apt-get install python3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "[1/3] Python已检测到: $($PYTHON_CMD --version)"
echo ""

# 检查依赖
echo "[2/3] 检查依赖..."
$PYTHON_CMD -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装Flask..."
    $PYTHON_CMD -m pip install flask flask-cors -q
fi
echo "依赖检查完成"
echo ""

# 获取IP地址
if command -v ipconfig &> /dev/null; then
    IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr eth0 2>/dev/null || echo "localhost")
elif command -v hostname &> /dev/null; then
    IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
else
    IP="localhost"
fi

# 启动服务器
echo "[3/3] 启动服务器..."
echo ""
echo "========================================"
echo "  服务器启动成功！"
echo "  本地访问: http://localhost:5000"
echo "  局域网访问: http://$IP:5000"
echo "========================================"
echo ""

# 尝试自动打开浏览器
if command -v open &> /dev/null; then
    echo "正在打开浏览器..."
    sleep 2 && open "http://localhost:5000" &
elif command -v xdg-open &> /dev/null; then
    echo "正在打开浏览器..."
    sleep 2 && xdg-open "http://localhost:5000" &
fi

echo "按 Ctrl+C 停止服务器"
echo ""

$PYTHON_CMD server.py
