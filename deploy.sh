#!/bin/bash
# PlaywriteOCR VPS一键部署脚本
# 用法: ./deploy.sh

set -e  # 遇到错误立即退出

echo "🚀 PlaywriteOCR 部署开始..."
echo "================================"

# 1. 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com | sh
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "✅ Docker安装完成"
fi

# 2. 检查Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装，正在安装..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose安装完成"
fi

# 3. 创建输出目录
mkdir -p output screenshots
echo "✅ 输出目录已创建"

# 4. 构建镜像
echo "📦 正在构建Docker镜像（首次约需5-10分钟）..."
docker compose build --no-cache

# 5. 启动服务
echo "🔄 正在启动服务..."
docker compose up -d

# 6. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 7. 检查健康状态
if curl -s http://localhost:9527/api/v1/health | grep -q "ok"; then
    echo ""
    echo "================================"
    echo "✅ 部署成功！"
    echo "================================"
    echo ""
    echo "📍 服务地址: http://$(hostname -I | awk '{print $1}'):9527"
    echo "📍 健康检查: http://localhost:9527/api/v1/health"
    echo "📍 API文档:  http://localhost:9527/api/v1/sources"
    echo ""
    echo "📋 常用命令:"
    echo "   查看日志: docker compose logs -f"
    echo "   重启服务: docker compose restart"
    echo "   停止服务: docker compose down"
    echo ""
else
    echo "⚠️ 服务可能还在启动中，请稍后检查:"
    echo "   docker compose logs"
fi
