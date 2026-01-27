# ASR Service with Speaker Diarization

This project is an automatic speech recognition service based on Whisper, with added speaker diarization functionality.

![App screenshot](doc/doc.PNG)

## Project Structure

```
ASRService/
├── app/                    # Application code
│   ├── main.py            # FastAPI application entry point
│   ├── asr_service.py     # Core ASR functionality
│   ├── auth.py            # Authentication module
│   ├── config.py          # Configuration settings
│   ├── logger.py          # Logging configuration
│   ├── metrics.py         # Prometheus metrics
│   ├── s3.py              # S3 storage integration
│   ├── static/            # Static files (CSS, JS)
│   └── templates/         # HTML templates
├── docker/                 # Docker configuration
│   ├── Dockerfile         # Docker image definition
│   ├── docker-compose.yml # Docker Compose configuration
│   └── start.sh           # Quick start script
├── doc/                   # Documentation
│   ├── doc.PNG           # Application screenshot
│   └── CHANGELOG.md      # Version history
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Features

- Speech-to-text (ASR)
- Multi-language support
- Speaker diarization
- RESTful API interface
- Web frontend for easy use
- Logging and auditing
- Prometheus monitoring metrics

## Installation

```bash
pip install -r requirements.txt
```

## Starting the Service

### Method 1: Using Docker (Recommended)

#### Prerequisites
- Docker installed
- Docker Compose installed

#### Quick Start

```bash
# Navigate to the docker directory
cd docker

# Run the startup script (Linux/Mac)
./start.sh

# Or manually start with docker-compose
docker-compose up -d
```

#### Docker Commands

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild the image
docker-compose build --no-cache
```

### Method 2: Manual Installation

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage

### Web Interface

After starting the service, visit `http://localhost:8000` in your browser to access the web interface. The interface has two main sections:

1. **Token Generation**: Click the "Generate New Token" button to obtain an API token for authentication.
2. **Audio Transcription**: Upload WAV or MP3 audio files and download the transcription results as JSON.

### API Endpoints

#### Get Access Token

```bash
curl -X POST http://localhost:8000/auth/token
```

#### Transcribe Audio

```bash
# Upload audio file
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.wav" \
  -F "language=en"

# Or provide audio URL
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_url=http://example.com/audio.wav" \
  -F "language=en"
```

## Response Format

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.58,
      "text": "Hello, world.",
      "speaker": "SPEAKER0"
    },
    {
      "start": 5.58,
      "end": 10.25,
      "text": "The weather is nice today.",
      "speaker": "SPEAKER1"
    }
  ]
}
```

## Environment Variables

### Docker Environment Variables

When using Docker, you can customize the service by setting environment variables in the `docker-compose.yml` file:

```yaml
environment:
  - WHISPER_MODEL_PATH=openai/whisper-large-v3
  - DIARIZATION_MODEL_PATH=pyannote/speaker-diarization-3.1
  - LOG_LEVEL=INFO
  - API_TOKENS=your_token_here,another_token
```

### Available Variables

- `WHISPER_MODEL_PATH`: Whisper模型路径 (默认: openai/whisper-large-v3)
- `DIARIZATION_MODEL_PATH`: 说话人分离模型路径 (默认: pyannote/speaker-diarization-3.1)
- `LOG_LEVEL`: 日志级别 (默认: INFO)
- `API_TOKENS`: 允许的API令牌列表 (逗号分隔)

## Speaker Diarization

This project integrates the PyAnnote.audio library to implement speaker diarization functionality. When processing audio, the system automatically detects different speakers and assigns corresponding speaker labels to each transcription segment.

## Development

The project follows a modular structure with clear separation of concerns:

- **app/main.py**: FastAPI application setup and routing
- **app/asr_service.py**: Core ASR and speaker diarization logic
- **app/auth.py**: Token-based authentication system
- **app/config.py**: Configuration management
- **app/logger.py**: Logging configuration
- **app/metrics.py**: Prometheus metrics collection
- **app/s3.py**: Optional S3 storage integration