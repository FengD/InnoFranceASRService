# ASR 服务 - 带说话人分离功能

本项目是基于 Whisper 的自动语音识别服务，增加了说话人分离功能。

![应用截图](doc/doc.PNG)

## 项目结构

```
ASRService/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 应用入口点
│   ├── asr_service.py     # 核心 ASR 功能
│   ├── auth.py            # 认证模块
│   ├── config.py          # 配置设置
│   ├── logger.py          # 日志配置
│   ├── metrics.py         # Prometheus 指标
│   ├── s3.py              # S3 存储集成
│   ├── static/            # 静态文件 (CSS, JS)
│   └── templates/         # HTML 模板
├── doc/                   # 文档
│   ├── doc.PNG           # 应用截图
│   └── CHANGELOG.md      # 版本历史
├── requirements.txt       # Python 依赖
├── .gitignore            # Git 忽略规则
└── README.md             # 英文文档
```

## 功能特性

- 语音转文本 (ASR)
- 多语言支持
- 说话人分离
- RESTful API 接口
- Web 前端界面
- 日志记录和审计
- Prometheus 监控指标

## 安装

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 使用方法

### Web 界面

启动服务后，在浏览器中访问 `http://localhost:8000` 即可使用 Web 界面。界面包含两个主要部分：

1. **令牌生成**：点击"生成新令牌"按钮获取用于认证的 API 令牌
2. **音频转录**：上传 WAV 或 MP3 音频文件，下载 JSON 格式的转录结果

### API 接口

#### 获取访问令牌

```bash
curl -X POST http://localhost:8000/auth/token
```

#### 转录音频

```bash
# 上传音频文件
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.wav" \
  -F "language=zh"

# 或提供音频 URL
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_url=http://example.com/audio.wav" \
  -F "language=zh"
```

## 响应格式

```json
{
  "language": "zh",
  "segments": [
    {
      "start": 0.0,
      "end": 5.58,
      "text": "你好，世界。",
      "speaker": "SPEAKER0"
    },
    {
      "start": 5.58,
      "end": 10.25,
      "text": "今天天气很好。",
      "speaker": "SPEAKER1"
    }
  ]
}
```

## 环境变量

- `WHISPER_MODEL_PATH`: Whisper 模型路径
- `DIARIZATION_MODEL_PATH`: 说话人分离模型路径 (默认: pyannote/speaker-diarization-3.1)
- `LOG_LEVEL`: 日志级别 (默认 INFO)
- `API_TOKENS`: 允许的 API 令牌列表 (逗号分隔)

## 说话人分离

本项目集成了 PyAnnote.audio 库来实现说话人分离功能。在处理音频时，系统会自动检测不同的说话人，并为每个转录片段分配相应的说话人标签。

## 开发说明

项目采用模块化结构，职责分离清晰：

- **app/main.py**: FastAPI 应用设置和路由
- **app/asr_service.py**: 核心 ASR 和说话人分离逻辑
- **app/auth.py**: 基于令牌的认证系统
- **app/config.py**: 配置管理
- **app/logger.py**: 日志配置
- **app/metrics.py**: Prometheus 指标收集
- **app/s3.py**: 可选的 S3 存储集成