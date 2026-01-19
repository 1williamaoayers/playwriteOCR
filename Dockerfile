# PlaywriteOCR 财经爬虫 Docker镜像
# 基于官方Playwright镜像，已包含浏览器

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# 设置工作目录
WORKDIR /app

# 设置时区为中国
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 显式安装对应版本的浏览器（修复自动升级导致的版本不匹配问题）
RUN playwright install chromium --with-deps

# 复制项目代码
COPY app.py .
COPY scrapers/ ./scrapers/

# 创建输出目录
RUN mkdir -p /app/output /app/screenshots

# 暴露端口
EXPOSE 9527

# 健康检查（每30秒检查一次API是否正常）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9527/api/v1/health || exit 1

# 启动命令
CMD ["python", "app.py"]
