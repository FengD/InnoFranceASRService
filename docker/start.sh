#!/bin/bash

# ASR Service Docker启动脚本
# 一键启动ASR服务

echo "🚀 启动ASR Service Docker容器..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 创建必要的目录
mkdir -p logs cache

echo "📦 构建Docker镜像..."
docker-compose build

echo "🔧 启动服务..."
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ ASR Service启动成功！"
    echo "🌐 服务地址: http://localhost:8000"
    echo "📊 监控地址: http://localhost:8000/metrics"
    echo ""
    echo "📝 使用说明:"
    echo "   1. 访问 http://localhost:8000 使用Web界面"
    echo "   2. 获取API Token: curl -X POST http://localhost:8000/auth/token"
    echo "   3. 查看日志: docker-compose logs -f"
    echo "   4. 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志"
    docker-compose logs
fi