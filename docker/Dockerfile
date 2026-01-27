# 使用官方Python运行时作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY ../requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY ../app ./app

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV WHISPER_MODEL_PATH=openai/whisper-large-v3
ENV DIARIZATION_MODEL_PATH=pyannote/speaker-diarization-3.1
ENV LOG_LEVEL=INFO

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]